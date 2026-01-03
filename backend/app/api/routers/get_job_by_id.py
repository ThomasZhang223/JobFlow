from fastapi import APIRouter, HTTPException

from app.schemas.database_tables import Job
from app.services.database_service import get_job_by_id
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_job_by_id/{job_id}", response_model=Job)
async def get_job_by_id_endpoint(job_id: int) -> Job:
    # Testing only
    user_id = settings.test_user_id
    
    try: 
        job = get_job_by_id(user_id,job_id)  
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    
    return job
