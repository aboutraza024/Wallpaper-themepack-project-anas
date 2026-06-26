"""
Application entrypoint.

Initializes logging, creates the FastAPI app, configures CORS, sets up
the MongoDB Motor client via a lifespan context, and includes the
categories/wallpapers routers.

Key changes from the MySQL version:
  • `@app.on_event("startup/shutdown")` replaced with the modern
    `lifespan` context manager (recommended in FastAPI 0.93+).
  • No `Base.metadata.create_all()` — MongoDB creates collections and
    indexes on first write; we only create explicit indexes here.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import (
    COL_CATEGORIES,
    COL_WALLPAPERS,
    close_mongo_connection,
    connect_to_mongo,
    get_client,
    ping_db,
)
from app.routes_categories import router as category_router
from app.routes_wallpapers import router as wallpaper_router
from app.utils import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup + shutdown in one place
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ────────────────────────────────────────────────────────────
    logger.info("Starting %s in %s mode", settings.PROJECT_NAME, settings.ENVIRONMENT)
    connect_to_mongo()

    await ping_db()
    logger.info("MongoDB connection verified.")

    # Create indexes (idempotent — safe to run on every startup)
    db = get_client()[settings.MONGODB_DB_NAME]
    await db[COL_CATEGORIES].create_index("name", unique=True)
    await db[COL_WALLPAPERS].create_index("category_id")
    logger.info("MongoDB indexes verified.")

    yield  # ← app runs here

    # ── shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down %s", settings.PROJECT_NAME)
    close_mongo_connection()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend for managing wallpapers, categories, themes, icons, "
        "and widgets for a mobile customization application."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallpaper_router, prefix=settings.API_V1_PREFIX)
app.include_router(category_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"], summary="Health check")
def root():
    """Basic health-check endpoint."""
    return {"success": True, "message": f"{settings.PROJECT_NAME} is running."}
