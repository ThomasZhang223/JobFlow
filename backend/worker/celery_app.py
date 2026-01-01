import redis
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.services import email_service
from app.schemas.messages import ScrapeUpdateMessage, Status

celery_app = Celery('jobflow', broker=settings.redis_url, backend=settings.redis_url)

def publish_update(message: ScrapeUpdateMessage):
    r = redis.from_url(settings.redis_url)
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
            email_service.send_scrape_complete_email(user_id, update.jobs_found, preferences)
        else:
            email_service.send_scrape_failed_email(user_id, update, preferences)

        return update.model_dump()

    except Exception as e:
        error_msg = str(e) if str(e) else "Unknown error"
        print(f"Scrape task failed: {error_msg}")

        update = ScrapeUpdateMessage(status=Status.FAILED, jobs_found=0, error_message=error_msg)
        publish_update(update)

        email_service.send_scrape_failed_email(user_id, update, preferences)

        return update.model_dump()
        
        
# THIS IS TEMPORARY EXAMPLE; WILL IMPLEMENT LATER
        
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('hello') every 30 seconds.
    # It uses the same signature of previous task, an explicit name is
    # defined to avoid this task replacing the previous one defined.
    sender.add_periodic_task(30.0, test.s('hello'), name='add every 30')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s('Happy Mondays!'),
    )

@celery_app.task
def test(arg):
    print(arg)

@celery_app.task
def add(x, y):
    z = x + y