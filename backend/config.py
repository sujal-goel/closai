"""
Configuration module using Pydantic Settings for type-safe environment variables.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from pydantic import model_validator
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    gemini_api_key: str = ""
    groq_api_key: str = ""
    mongodb_uri: str = ""
    mongodb_user: str = ""
    mongodb_password: str = ""
    mongodb_cluster: str = ""
    mongodb_db: str = "cloud_compare"
    tavily_api_key: str =  "" 
    gcp_billing_api_key: str = ""
    frontend_url: str = "http://localhost:3000"
    db_name: str = "cloud_compare"
    deep_sync_threshold_days: int = 7

    @model_validator(mode="after")
    def assemble_mongodb_uri(self) -> "Settings":
        # If full URI is provided, use it. Otherwise, build it from components.
        if not self.mongodb_uri and self.mongodb_user and self.mongodb_password and self.mongodb_cluster:
            user = quote_plus(self.mongodb_user)
            pw = quote_plus(self.mongodb_password)
            self.mongodb_uri = f"mongodb+srv://{user}:{pw}@{self.mongodb_cluster}/{self.mongodb_db}"
        
        # Default fallback if nothing is provided
        if not self.mongodb_uri:
            self.mongodb_uri = "mongodb://localhost:27017/cloud_compare"
            
        return self
    
    @property
    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key and self.tavily_api_key.strip())

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.strip())

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()
