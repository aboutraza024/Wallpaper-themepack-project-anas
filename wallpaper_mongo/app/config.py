"""
App settings.

All configuration values are read from environment variables (and from
the .env file in the project root). Replace MONGODB_URL in .env to
point the app at a different database — no code changes needed.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings in one place."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "Wallpaper Management Backend"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # ------------------------------------------------------------------
    # MongoDB
    # Local  : mongodb://localhost:27017
    # Atlas  : mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
    # ------------------------------------------------------------------
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB_NAME: str = Field(default="wallpaper_db")

    # ------------------------------------------------------------------
    # AWS S3 (Mocked for now - future-ready)
    # ------------------------------------------------------------------
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_REGION: str = Field(default="us-east-1")
    AWS_BUCKET_NAME: str = Field(default="dummy-s3-bucket")
    USE_MOCK_S3: bool = Field(default=True)

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of Settings."""
    return Settings()


settings = get_settings()
