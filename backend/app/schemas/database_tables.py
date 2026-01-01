from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ScrapeLength(int, Enum):
    SHORT = 25      # ~25 jobs (2-3 pages, ~3-4 minutes)
    MEDIUM = 50     # ~50 jobs (4-5 pages, ~6-8 minutes)
    LONG = 100      # ~100 jobs (8-10 pages, ~10-12 minutes)


class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company_name: str
    location: str
    job_type: str
    salary: Optional[str] = None
    url: str
    posted_date: Optional[str] = None
    description: str = None

class Preference(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    scrape_length: Optional[int] = ScrapeLength.MEDIUM