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
    scrape_update_chanel: str = "scrape_update"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()