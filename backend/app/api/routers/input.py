from fastapi import APIRouter, HTTPException, Body

router = APIRouter(prefix="/api", tags=['Testing'])

@router.post("/test")
async def get_text(text: str = Body(...)) -> str:
    if len(text) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    return_str = f'Your input was: {text}'
    
    return return_str
