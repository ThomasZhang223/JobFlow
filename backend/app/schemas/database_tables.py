from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ScrapeLength(int, Enum):
    SHORT = 50      
    MEDIUM = 150     
    LONG = 250      


class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company_name: str
    location: str
    job_type: str
    salary: Optional[str] = None
    url: str
    description: Optional[str] = None
    benefits: Optional[str] = None
    priority: Optional[bool] = False

class Preference(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    benefits: Optional[str] = None
    radius: Optional[int] = None
    scrape_length: Optional[int] = ScrapeLength.MEDIUM
    
class Statistics(BaseModel):
    total_jobs: int = 0
    current_jobs: int = 0
    saved_jobs: int = 0
    completed_jobs: int = 0
    total_scrapes: int = 0
    latest_scrape: Optional[str] = None