from fastapi import APIRouter, HTTPException, Depends

from app.services.database_service import delete_job_by_id as delete_job_from_db
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.delete("/delete_job_by_id/{job_id}")
async def delete_job_by_id(
    job_id: int,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    try:
        delete_job_from_db(user_id, job_id)
        return {"detail": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))