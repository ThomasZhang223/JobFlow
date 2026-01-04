from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, Depends

from app.core.websocket_manager import websocket_manager
from app.core.auth import get_websocket_user_id

router = APIRouter(prefix="/ws", tags=['Websocket'])

@router.websocket("/scrape")
async def scrape_websocket(
    websocket: WebSocket,
    user_id: str = Depends(get_websocket_user_id)
):
    """
    WebSocket endpoint for scrape updates
    Requires JWT token as query parameter: ws://localhost:8000/ws/scrape?token=xxx
    """
    await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
    except WebSocketException as e:
        print(f"WebSocket exception: {e}")
        websocket_manager.disconnect(user_id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        websocket_manager.disconnect(user_id)