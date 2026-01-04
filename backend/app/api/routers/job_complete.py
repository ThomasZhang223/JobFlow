from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Job
from app.services.database_service import update_completed
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/job_complete/{job_id}")
async def get_job_by_id_endpoint(
    job_id: int,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    try:
        update_completed(user_id, job_id)
        return {"detail": "Statistics updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
