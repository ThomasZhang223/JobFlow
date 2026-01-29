from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import ValidationError

from app.core.config import settings
from app.api.routers import (health, scrape, delete_job_by_id, get_job_by_id, \
    get_jobs, get_preferences, get_priority_jobs, get_statistics, job_complete, \
        search_jobs, toggle_job_priority, update_preference)        
    
from app.api import websocket
from app.schemas.messages import ScrapeUpdateMessage
from app.core.redis_client import redis_client
from app.core.websocket_manager import websocket_manager

async def handle_scrape_update(message: dict):
    # Validate message recieved from Celery with schema, then forward to websocket
    print(f"📨 Received scrape update: {message}")  # Debug log
    try:
        update = ScrapeUpdateMessage.model_validate(message)
    except ValidationError as e:
        print(f'Invalid message: {e}')
        return

    # Extract user_id from message
    user_id = message.get('user_id')
    if not user_id:
        print(f'No user_id in scrape update message')
        return

    await websocket_manager.send_to_user(user_id=user_id, message=update.model_dump(mode='json'))
    
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("\nStart API\n")

    try:
        await redis_client.connect()
        await redis_client.subscribe(settings.scrape_update_channel, handle_scrape_update)
        print("Redis pub/sub initialized successfully\n")
    except ConnectionError as e:
        print(f"\n⚠️  CRITICAL: Redis connection failed during startup")
        print(f"Error: {e}")
        raise

    # MAIN PROGRAM FLOW
    yield

    # SHUTDOWN
    await redis_client.disconnect()
    print("\nShutdown API\n")

app = FastAPI (
    title = "JobFlow",
    description = "Auto job application",
    version = "1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints here
app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(websocket.router)

app.include_router(delete_job_by_id.router)
app.include_router(get_job_by_id.router)
app.include_router(get_jobs.router)
app.include_router(get_preferences.router)
app.include_router(get_priority_jobs.router)
app.include_router(get_statistics.router)
app.include_router(job_complete.router)
app.include_router(search_jobs.router)
app.include_router(toggle_job_priority.router)
app.include_router(update_preference.router)