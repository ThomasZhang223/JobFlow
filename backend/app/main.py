from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import ValidationError

from app.core.config import settings
from app.api.routers import health, input
from app.api import websocket
from app.schemas.messages import ScrapeUpdateMessage
from app.core.redis_client import redis_client
from app.core.websocket_manager import WebSocketManager

async def handle_scrape_update(message: dict):
    # Validate message recieved from Celery with schema, then forward to websocket
    try: 
        update = ScrapeUpdateMessage.model_validate(message)
    except ValidationError as e:
        print(f'Invalid message: {e}')
    
    await WebSocketManager.broadcast(message)
    
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("Start API")
    
    await redis_client.connect()
    await redis_client.subscribe("scrape_updates", handle_scrape_update)
    
    # MAIN PROGRAM FLOW
    yield
    
    # SHUTDOWN
    await redis_client.disconnect()
    print("Shutdown API")

app = FastAPI (
    title = "MASA",
    description = "Auto job application",
    version = "1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints here
app.include_router(health.router)
app.include_router(input.router)
app.include_router(websocket.router)
