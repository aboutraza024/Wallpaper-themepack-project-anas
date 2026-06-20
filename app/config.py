"""
App settings.

All configuration values are read from environment variables (and from
the .env file in the project root). If you need to point the app at a
different database, just edit DATABASE_URL in your .env file — you
don't need to touch any code.
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
    # Database (MySQL) — just put your full connection URL in .env
    # Example: mysql+pymysql://root:password@localhost:3306/wallpaper_db
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:@localhost:3306/wallpaper_db"
    )

    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_RECYCLE: int = Field(default=3600)
    DB_ECHO: bool = Field(default=False)

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
