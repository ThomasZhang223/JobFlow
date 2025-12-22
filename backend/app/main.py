from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .routers import health, input

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Start API")
    yield
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

