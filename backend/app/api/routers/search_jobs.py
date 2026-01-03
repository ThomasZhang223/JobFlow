from fastapi import APIRouter, HTTPException, Query

from app.schemas.database_tables import Job
from app.services.database_service import search_jobs
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/search_jobs", response_model=list[Job])
async def search_jobs_endpoint(q: str = Query(..., description="Search query")) -> list[Job]:
    # Testing only
    user_id = settings.test_user_id

    try:
        jobs = search_jobs(user_id, q)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    if not jobs:
        return []

    return jobs