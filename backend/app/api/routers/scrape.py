from fastapi import APIRouter, HTTPException

from app.schemas.messages import ScrapeUpdateMessage, Status
from app.services.database_service import get_preferences
from app.core.config import settings
from worker.celery_app import run_scrape

router = APIRouter(prefix="/api", tags=['Scraping'])

@router.post("/scrape", response_model=ScrapeUpdateMessage)
async def scrape() -> ScrapeUpdateMessage:
    # Testing only
    user_id = settings.test_user_id
    
    preferences = get_preferences(user_id)
    if preferences is None:
        raise HTTPException(status_code=400, detail="No preferences set")
    
    run_scrape.delay(user_id,preferences.model_dump())
    
    update = ScrapeUpdateMessage(status=Status.PENDING, jobs_found=0)
    
    return update
