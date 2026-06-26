"""
Database setup — Motor (async MongoDB driver).

Exposes:
  • `client`       — the shared AsyncIOMotorClient (created at startup)
  • `get_db()`     — FastAPI dependency that yields the Motor database object
  • `ping_db()`    — lightweight connectivity check called at startup
  • Collection name constants used across crud.py
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

# ---------------------------------------------------------------------------
# Collection name constants
# Keep these here so they are never mistyped as bare strings in crud.py.
# ---------------------------------------------------------------------------
COL_CATEGORIES = "categories"
COL_WALLPAPERS = "wallpapers"

# ---------------------------------------------------------------------------
# Shared client — created once at startup, closed at shutdown (see main.py)
# ---------------------------------------------------------------------------
_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    """Return the module-level Motor client (must be started first)."""
    if _client is None:
        raise RuntimeError("MongoDB client has not been initialised yet.")
    return _client


def connect_to_mongo() -> None:
    """Create the Motor client.  Called inside the FastAPI lifespan startup."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URL)


def close_mongo_connection() -> None:
    """Close the Motor client.  Called inside the FastAPI lifespan shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_db() -> None:
    """Send a ping command to verify the connection is alive."""
    await get_client()[settings.MONGODB_DB_NAME].command("ping")


async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency — yields the Motor database object.

    Usage in a route:
        async def my_route(db: AsyncIOMotorDatabase = Depends(get_db)):
            ...
    """
    yield get_client()[settings.MONGODB_DB_NAME]
