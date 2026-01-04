from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Job
from app.services.database_service import get_priority_jobs
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_priority_jobs", response_model=list[Job])
async def get_priority_jobs_endpoint(user_id: str = Depends(get_current_user_id)) -> list[Job]:
    try:
        priority_jobs = get_priority_jobs(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    if not priority_jobs:
        return []

    return priority_jobs