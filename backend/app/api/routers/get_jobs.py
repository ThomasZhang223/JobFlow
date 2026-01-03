from fastapi import APIRouter, HTTPException

from app.schemas.database_tables import Job
from app.services.database_service import get_jobs as get_jobs_from_db
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_jobs", response_model=list[Job])
async def get_jobs() -> list[Job]:
    # Testing only
    user_id = settings.test_user_id
    
    try:
        jobs = get_jobs_from_db(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    
    if not jobs:
        return []
    
    return jobs
