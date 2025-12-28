from fastapi import APIRouter
from datetime import date

router = APIRouter(prefix="/api", tags=["Testing"])

@router.get("/health")
async def get_health():
    return {
        "status": "healthy",
        "timestamp": date.today(),
    }
    