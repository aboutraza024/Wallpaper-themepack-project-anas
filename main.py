"""
Application entrypoint.

Initializes logging, creates the FastAPI app, configures CORS,
and includes the categories/wallpapers routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes_categories import router as category_router
from app.routes_wallpapers import router as wallpaper_router
from app.utils import get_logger, setup_logging

# Import the models module so every table is registered on Base.metadata
# before create_all() is called below.
import app.models  # noqa: F401

setup_logging()
logger = get_logger(__name__)

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


@app.on_event("startup")
def on_startup():
    logger.info("Starting %s in %s mode", settings.PROJECT_NAME, settings.ENVIRONMENT)
    # Creates any tables that don't already exist. Simple and dependency-free
    # alternative to running migrations for this project.
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down %s", settings.PROJECT_NAME)
