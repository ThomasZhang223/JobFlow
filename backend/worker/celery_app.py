import redis
import time
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.services import database_service, email_service
from app.schemas.database_tables import Job
from app.schemas.messages import ScrapeUpdateMessage, Status

celery_app = Celery('jobflow', broker=settings.redis_url, backend=settings.redis_url)

def publish_update(message: ScrapeUpdateMessage):
    r = redis.from_url(settings.redis_url)
    r.publish(settings.scrape_update_channel, message.model_dump_json())
    r.close()
    
@celery_app.task
def run_scrape(user_id: str, preferences: dict):
    update = ScrapeUpdateMessage(status=Status.RUNNING, jobs_found=0)
    publish_update(update)
    
    try:
        time.sleep(5)
        
        job = Job(title='Senior Software Engineer', company_name='Google',
                  location='Mountain View', job_type='Full-time',
                  url="https://www.google.com/about/careers/applications/jobs/results/")
        
        database_service.create_job(user_id, job)
        
        update = ScrapeUpdateMessage(status=Status.COMPLETED, jobs_found=1)
        publish_update(update)
        
        email_service.send_scrape_complete_email(user_id, update)
    
    except Exception as e:
        error_msg = str(e) if str(e) else "Unknown error"
        print(f"Scrape failed: {error_msg}") 
        
        update = ScrapeUpdateMessage(status=Status.FAILED, jobs_found=0, error_message=error_msg)
        publish_update(update)    
        
        email_service.send_scrape_failed_email(user_id, update)