from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Preference
from app.services.database_service import get_preferences
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.get("/get_preferences", response_model=Preference)
async def get_preferences_endpoint(user_id: str = Depends(get_current_user_id)) -> Preference:
    try:
        preferences = get_preferences(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    if not preferences:
        # Return default empty preferences if user has no data yet
        return Preference()

    return preferences
