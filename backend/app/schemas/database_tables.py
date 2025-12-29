from pydantic import BaseModel
from typing import Optional

class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company_name: str
    location: str
    job_type: str
    salary: Optional[str] = None
    url: str
    posted_date: Optional[str] = None

class Preference(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None