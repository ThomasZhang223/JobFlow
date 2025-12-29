from pydantic import BaseModel
from enum import Enum
from typing import Optional

class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    
class ScrapeUpdateMessage(BaseModel):
    """
    Message published to Redis when scrape task status changes.
    Used by: Celery (publish), FastAPI (receive)
    """
    status: Status
    jobs_found: int = 0
    error_message: Optional[str] = None