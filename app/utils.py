"""
Small shared helpers used across the app:
  - logging setup
  - the standard {"success", "message", "data"} JSON response envelope
  - a couple of constants used by the file-upload endpoint
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from app.config import settings

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configures console + rotating file logging. Call once at startup."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    if root_logger.handlers:
        return  # avoid duplicate handlers when the dev server auto-reloads

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Returns a module-scoped logger, e.g. get_logger(__name__)."""
    return logging.getLogger(name)


# ----------------------------------------------------------------------
# Standard JSON response envelope
#
# Every endpoint returns the same simple shape:
# {"success": true, "message": "...", "data": {...} | [...]}
# ----------------------------------------------------------------------
def success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
) -> dict:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, errors: Optional[Any] = None) -> dict:
    return {"success": False, "message": message, "errors": errors}


# ----------------------------------------------------------------------
# File upload constants
# ----------------------------------------------------------------------
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}

MAX_UPLOAD_FILE_SIZE_MB = 10
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

S3_UPLOAD_FOLDERS = {
    "home_wallpaper": "wallpapers/home",
    "lock_wallpaper": "wallpapers/lock",
    "theme": "themes",
    "icon": "icons",
    "widget": "widgets",
}
