"""
App configuration settings
Loads settings from .env
"""

from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Frontend url
    allowed_origins: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    scrape_update_channel: str = "scrape_update"
    
    # Database
    supabase_url: str
    supabase_key: str
    
    # Email
    resend_api_key: str
    
    # Testing
    test_user_id : str = 'd1f7418b-f9a5-4adb-b8f9-e5128952a8a2'
    test_from_email: str = 'onboarding@resend.dev'

    # Scraper
    scraper_timeout_seconds: int = 300  # 5 minutes
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()