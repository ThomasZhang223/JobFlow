from fastapi import APIRouter, HTTPException

from app.schemas.database_tables import Job
from app.services.database_service import get_priority_jobs
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_priority_jobs", response_model=list[Job])
async def get_priority_jobs_endpoint() -> list[Job]:
    # Testing only
    user_id = settings.test_user_id

    try:
        priority_jobs = get_priority_jobs(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    if not priority_jobs:
        return []

    return priority_jobs