from fastapi import APIRouter, HTTPException, Depends

from app.schemas.database_tables import Preference
from app.services.database_service import update_preference
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.put("/update_preferences")
async def update_preferences(
    preference: Preference,
    user_id: str = Depends(get_current_user_id)
) -> dict:
    try:
        update_preference(user_id, preference)
        return {"detail": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))