from fastapi import APIRouter, HTTPException, Depends

from app.services.database_service import toggle_job_priority
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.put("/toggle_job_priority/{job_id}")
async def toggle_job_priority_endpoint(
    job_id: int,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    try:
        success = toggle_job_priority(user_id, job_id)
        if success:
            return {"detail": "Job priority toggled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))