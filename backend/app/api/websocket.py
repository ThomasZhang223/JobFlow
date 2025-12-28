from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException

from app.core.websocket_manager import WebSocketManager

router = APIRouter(prefix="/ws", tags=['Websocket'])

@router.websocket("/scrape")
async def scrape_websocket(websocket: WebSocket):
    await WebSocketManager.connect(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        WebSocketManager.disconnect(websocket)
    except WebSocketException as e:
        print(f"WebSocket exception: {e}")
        WebSocketManager.disconnect(websocket)
    except Exception as e:
        print(f"Unexpected error: {e}")
        WebSocketManager.disconnect(websocket)