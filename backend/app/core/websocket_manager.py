"""
Simplified WebSocket connection manager
Stores ONE connection per user in-memory (single server only)
"""

from fastapi import WebSocket
from typing import Dict

class WebSocketManager:
    def __init__(self):
        # Simple dictionary: {user_id: websocket}
        # Only ONE connection per user
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept and store ONE WebSocket connection per user
        If user already has a connection, disconnect the old one

        Args:
            websocket: The WebSocket connection
            user_id: The authenticated user's ID
        """
        # If user already connected, close old connection
        if user_id in self.connections:
            old_ws = self.connections[user_id]
            try:
                await old_ws.close(code=1000, reason="New connection established")
            except:
                pass  # Old connection already closed
            print(f"User {user_id} reconnected. Closed old connection.")

        # Accept new connection
        await websocket.accept()

        # Store connection
        self.connections[user_id] = websocket

        print(f'WebSocket connected for user {user_id}. Total connections: {len(self.connections)}')

    def disconnect(self, user_id: str):
        """
        Remove a WebSocket connection for a specific user

        Args:
            user_id: The user's ID
        """
        if user_id in self.connections:
            del self.connections[user_id]
            print(f'WebSocket disconnected for user {user_id}. Remaining: {len(self.connections)}')

    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to a specific user's connection

        Args:
            user_id: The user to send message to
            message: The message dictionary to send
        """
        if user_id not in self.connections:
            print(f"User {user_id} is not connected")
            return

        websocket = self.connections[user_id]

        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f'Error sending to user {user_id}: {e}')
            # Connection failed, clean up
            self.disconnect(user_id)

    def debug_connections(self):
        """Print current connection status for debugging"""
        print(f"Active WebSocket connections: {len(self.connections)}")
        print(f"Connected users: {list(self.connections.keys())}")

# Global instance
websocket_manager = WebSocketManager()
