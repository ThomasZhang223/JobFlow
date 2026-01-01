"""
Integrated Scraper Service for JobFlow
Runs Indeed spider with user preferences and provides real-time updates via Redis
"""

import redis
import sys
import os
import json
import subprocess
import time

# Add paths for imports
current_dir = os.path.dirname(__file__)
backend_dir = os.path.join(current_dir, '..')

# Add backend directory to path for app imports
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.schemas.messages import ScrapeUpdateMessage, Status
from app.schemas.database_tables import Job, ScrapeLength
from app.services import database_service


def publish_update(message: ScrapeUpdateMessage):
    """Publish scrape update to Redis for real-time frontend updates"""
    r = redis.from_url(settings.redis_url)
    r.publish(settings.scrape_update_channel, message.model_dump_json())
    r.close()


def run_scraper_with_preferences(user_id: str, preferences: dict) -> ScrapeUpdateMessage:
    """
    Main function to run scraper with user preferences using subprocess
    Called by celery_app.py run_scrape task

    Args:
        user_id: User ID for database storage
        preferences: Dict with title, location, job_type, salary, description, scrape_length

    Returns:
        ScrapeUpdateMessage: Final status with job count or error
    """

    # Determine max_results from scrape_length preference
    max_results = preferences.get('scrape_length')

    try:
        # Send initial running status
        update = ScrapeUpdateMessage(status=Status.RUNNING, jobs_found=0)
        publish_update(update)

        # Validate required preferences
        if not preferences.get('title') or not preferences.get('location'):
            error_msg = "Missing required preferences: title and location must be provided"
            error_update = ScrapeUpdateMessage(
                status=Status.FAILED,
                jobs_found=0,
                error_message=error_msg
            )
            publish_update(error_update)
            return error_update

        # Run spider via subprocess to avoid import conflicts
        spider_script = os.path.join(current_dir, 'run_spider.py')
        preferences_json = json.dumps(preferences)

        print(f"Running spider subprocess with preferences: {preferences_json}")

        # Run spider subprocess
        # Pass only essential settings to subprocess via environment variables
        env = os.environ.copy()
        env['REDIS_URL'] = settings.redis_url
        env['SCRAPE_UPDATE_CHANNEL'] = settings.scrape_update_channel
        env['SCRAPER_USER_ID'] = user_id  # Pass user_id to subprocess
        env['SUPABASE_URL'] = settings.supabase_url
        env['SUPABASE_KEY'] = settings.supabase_key

        # Use Popen for real-time output streaming
        print("=== STARTING SPIDER SUBPROCESS ===")
        process = subprocess.Popen([
            sys.executable, '-u', spider_script,  # -u flag for unbuffered output
            preferences_json,
            str(max_results)
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, bufsize=1)

        # Listen for Redis messages from spider to get final job count
        r = redis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        pubsub.subscribe(settings.scrape_update_channel)

        final_job_count = 0
        spider_completed = False

        try:
            # Poll for both subprocess completion and Redis messages
            while process.poll() is None and not spider_completed:
                # Check for Redis messages with timeout
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        update_data = json.loads(message['data'])
                        print(f"REDIS UPDATE: {update_data}")

                        # Check if this is the final completion message
                        if update_data.get('spider_finished'):
                            final_job_count = update_data.get('jobs_found', 0)
                            spider_completed = True
                            print(f"Spider finished with {final_job_count} jobs")
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Failed to parse Redis message: {e}")

            # Wait for subprocess to complete
            process.wait(timeout=settings.scraper_timeout_seconds)
            returncode = process.returncode

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            print("=== SPIDER SUBPROCESS TIMED OUT ===")
            returncode = 1
        finally:
            pubsub.close()
            r.close()

        print("=== SPIDER SUBPROCESS FINISHED ===")

        if returncode != 0:
            error_msg = f"Spider subprocess failed with return code {returncode}"
            error_update = ScrapeUpdateMessage(
                status=Status.FAILED,
                jobs_found=0,
                error_message=error_msg
            )
            return error_update

        # Return final job count from Redis message
        completion_update = ScrapeUpdateMessage(
            status=Status.COMPLETED,
            jobs_found=final_job_count
        )
        return completion_update

    except subprocess.TimeoutExpired:
        error_msg = "Spider timed out after 10 minutes"
        error_update = ScrapeUpdateMessage(
            status=Status.FAILED,
            jobs_found=0,
            error_message=error_msg
        )
        publish_update(error_update)
        return error_update

    except Exception as e:
        error_msg = f"Scraper failed: {str(e)}"
        print(f"Error: {error_msg}")

        error_update = ScrapeUpdateMessage(
            status=Status.FAILED,
            jobs_found=0,
            error_message=error_msg
        )
        publish_update(error_update)
        return error_update