from fastapi import APIRouter, HTTPException

from app.schemas.database_tables import Job
from app.services.database_service import update_completed
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/job_complete/{job_id}")
async def get_job_by_id_endpoint(job_id: int) -> dict:
    # Testing only
    user_id = settings.test_user_id
    
    try: 
        update_completed(user_id, job_id) 
        return {"detail": "Statistics updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
