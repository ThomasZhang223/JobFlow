from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException

from app.core.websocket_manager import websocket_manager

router = APIRouter(prefix="/ws", tags=['Websocket'])

@router.websocket("/scrape")
async def scrape_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except WebSocketException as e:
        print(f"WebSocket exception: {e}")
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"Unexpected error: {e}")
        websocket_manager.disconnect(websocket)