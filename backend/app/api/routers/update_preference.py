from fastapi import APIRouter, HTTPException

from app.schemas.database_tables import Preference
from app.services.database_service import update_preference
from app.core.config import settings

router = APIRouter(prefix="/api", tags=['Frontend'])

@router.put("/update_preferences")
async def update_preferences(preference: Preference) -> dict:
    # Testing only
    user_id = settings.test_user_id

    try:
        update_preference(user_id, preference)
        return {"detail": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))