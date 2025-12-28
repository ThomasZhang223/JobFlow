from fastapi import WebSocket
import json 

class WebSocketManager:
    
    def __init__(self):
        # Just one global connection for MVP
        self.connection = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connection = websocket
        print(f'Websocket connected at {websocket}')
        
    async def disconnect(self, websocket: WebSocket):
        self.connection = None
    
    async def broadcast(self, message: dict):
        if self.connect is None:
            print("No websocket connection active")
            return
        try:
            await self.connection.send_json(message)
        except Exception as e:
            print(f'Websocket broadcast error: {e}')
            
websocket_manager = WebSocketManager()