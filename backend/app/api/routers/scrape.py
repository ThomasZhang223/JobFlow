from fastapi import APIRouter, HTTPException, Depends

from app.schemas.messages import ScrapeUpdateMessage, Status
from app.services.database_service import get_preferences
from app.core.auth import get_current_user_id
from worker.celery_app import run_scrape

router = APIRouter(prefix="/api", tags=['Scraping'])

@router.post("/scrape", response_model=ScrapeUpdateMessage)
async def scrape(user_id: str = Depends(get_current_user_id)) -> ScrapeUpdateMessage:
    preferences = get_preferences(user_id)
    if preferences is None:
        raise HTTPException(status_code=400, detail="No preferences set")

    run_scrape.delay(user_id, preferences.model_dump())

    update = ScrapeUpdateMessage(status=Status.PENDING, jobs_found=0)

    return update
