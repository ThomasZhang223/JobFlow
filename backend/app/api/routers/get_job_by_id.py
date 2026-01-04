from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Job
from app.services.database_service import get_job_by_id
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_job_by_id/{job_id}", response_model=Job)
async def get_job_by_id_endpoint(
    job_id: int,
    user_id: str = Depends(get_current_user_id)
) -> Job:
    try:
        job = get_job_by_id(user_id, job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    return job
