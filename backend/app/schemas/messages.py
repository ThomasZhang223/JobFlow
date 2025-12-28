from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    
class ScrapeUpdateMessage(BaseModel):
    """
    Message published to Redis when scrape task status changes.
    Used by: Celery (publish), FastAPI (receive)
    """
    task_id: str
    status: Status
    jobs_found: int = 0
    error_message: Optional[str] = None
    
class ScrapeCompletionResults(BaseModel):
    pass