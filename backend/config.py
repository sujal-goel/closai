"""
Configuration module using Pydantic Settings for type-safe environment variables.
"""
from pydantic_core.core_schema import model_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    gemini_api_key: str = ""
    groq_api_key: str = ""
    mongodb_uri: str = "mongodb://localhost:27017/cloud_compare"
    tavily_api_key: str =  "" 
    frontend_url: str = "http://localhost:3000"
    db_name: str = "cloud_compare"

    @property
    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key and self.tavily_api_key.strip())

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.strip())

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()
