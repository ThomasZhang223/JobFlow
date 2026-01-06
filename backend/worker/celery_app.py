import redis
import asyncio
from celery import Celery

from app.core.config import settings
from app.services import email_service
from app.schemas.messages import ScrapeUpdateMessage, Status

connection_link = f"rediss://:{settings.upstash_redis_rest_token}@{settings.upstash_redis_rest_url[8:]}:{settings.upstash_redis_port}?ssl_cert_reqs=required"
celery_app = Celery('jobflow', broker=connection_link, backend=connection_link)

def publish_update(message: ScrapeUpdateMessage):
    r = redis.from_url(connection_link)
    r.publish(settings.scrape_update_channel, message.model_dump_json())
    r.close()
    
@celery_app.task
def run_scrape(user_id: str, preferences: dict):
    try:
        # Add the backend directory to Python path for imports
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from worker/ to backend/
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from scraper.scraper_service import run_scraper_with_preferences

        # Run the integrated scraper service (uses scrape_length from preferences)
        update = run_scraper_with_preferences(user_id, preferences)

        # Send email notification based on result
        if update.status == Status.COMPLETED:
            asyncio.run(email_service.send_scrape_complete_email(user_id, update.jobs_found, preferences))
        else:
            asyncio.run(email_service.send_scrape_failed_email(user_id, update, preferences))

        return update.model_dump()

    except Exception as e:
        error_msg = str(e) if str(e) else "Unknown error"
        print(f"Scrape task failed: {error_msg}")

        update = ScrapeUpdateMessage(status=Status.FAILED, jobs_found=0, error_message=error_msg)
        publish_update(update)

        asyncio.run(email_service.send_scrape_failed_email(user_id, update, preferences))

        return update.model_dump()