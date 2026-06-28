"""
Application configuration — loads from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # App
    APP_NAME: str = "DSR Petrol Platform"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-in-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5500"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Gemini AI
    GEMINI_API_KEY: str = ""

    # OCR
    OCR_CONFIDENCE_THRESHOLD: float = 0.85
    OCR_HIGH_CONFIDENCE: float = 0.95
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
