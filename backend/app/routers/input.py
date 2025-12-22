from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=['Testing'])

@router.post("/test", responses=str)
async def get_text(text: str) -> str:
    if len(text) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    return_str = f'Your input was: {text}'
    
    return return_str
