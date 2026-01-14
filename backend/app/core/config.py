"""
App configuration settings
Loads settings from .env
"""

import json
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Frontend url (JSON array format: ["http://localhost:3000","https://example.com"])
    allowed_origins: str

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse JSON array of origins into a list"""
        return json.loads(self.allowed_origins)

    # Redis - Upstash
    upstash_redis_port: int 
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str
    scrape_update_channel: str = "scrape_update"
    
    # Database
    supabase_url: str
    supabase_key: str
    
    # Email
    email_password: str
    
    # Proxies
    proxy_str: str
    
    @property
    def proxies_list(self) -> list[str]:
        """Parse JSON array of origins into a list"""
        return json.loads(self.proxy_str)
    
    proxy_username: str
    proxy_password: str
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()