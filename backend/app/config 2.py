"""
App configuration settings
Loads settings from .env
"""

from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Define all config settings here
    allowed_origins: list[str]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()