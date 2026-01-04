from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Statistics
from app.services.database_service import get_user_statistics
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_statistics", response_model=Statistics)
async def get_statistics(user_id: str = Depends(get_current_user_id)) -> Statistics:
    try:
        statistics = get_user_statistics(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    if not statistics:
        # Return default statistics if user has no data yet
        return Statistics()

    return statistics
