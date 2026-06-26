"""API routes for Wallpaper resources (create, read, update, delete, upload)."""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import crud
from app.database import get_db
from app.s3_service import S3Service, get_s3_service
from app.schemas import (
    UploadResponse,
    WallpaperCreateRequest,
    WallpaperResponse,
    WallpaperUpdateRequest,
)
from app.utils import S3_UPLOAD_FOLDERS, success_response

router = APIRouter(prefix="/wallpapers", tags=["Wallpapers"])


# ---------------------------------------------------------------------------
# File Upload
# ---------------------------------------------------------------------------
@router.post(
    "/upload",
    summary="Upload a wallpaper-related image file and receive its (mock) S3 URL",
    response_model=None,
)
async def upload_wallpaper_asset(
    file: UploadFile = File(...),
    asset_type: str = Query(
        default="home_wallpaper",
        description="One of: home_wallpaper, lock_wallpaper, theme, icon, widget",
    ),
    s3_service: S3Service = Depends(get_s3_service),
):
    """
    Uploads a single file and returns the resulting URL.
    The URL can be passed into the create/update wallpaper payloads.
    """
    folder = S3_UPLOAD_FOLDERS.get(asset_type, "uploads")
    url = await s3_service.upload_file(file, folder=folder)
    data = UploadResponse(url=url, filename=file.filename)
    return success_response(data=data, message="File uploaded successfully")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
@router.post(
    "",
    summary="Create a wallpaper (with optional themes, icons, widgets)",
    response_model=None,
    status_code=201,
)
async def create_wallpaper(
    payload: WallpaperCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Creates a wallpaper. If the given category name already exists it is
    reused; otherwise a new category is created automatically.
    """
    wallpaper_dict = await crud.create_wallpaper(db, payload)
    data = WallpaperResponse(**wallpaper_dict)
    return success_response(data=data, message="Wallpaper created successfully")


# ---------------------------------------------------------------------------
# Get details
# ---------------------------------------------------------------------------
@router.get(
    "/{wallpaper_id}",
    summary="Get full wallpaper details (with nested themes, icons, widgets)",
    response_model=None,
)
async def get_wallpaper(
    wallpaper_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    wallpaper_dict = await crud.get_wallpaper_or_404(db, wallpaper_id)
    data = WallpaperResponse(**wallpaper_dict)
    return success_response(data=data, message="Wallpaper fetched successfully")


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------
@router.put(
    "",
    summary="Update a wallpaper (wallpaper_id body mein dein)",
    response_model=None,
)
async def update_wallpaper(
    payload: WallpaperUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    wallpaper_id request body mein dena zaroori hai (URL mein nahi).

    Sirf jo fields bhejo woh update hongi — baaki fields untouched rahengi.
    Themes / icons / widgets ke liye:
      - id omit karo  → naya add hoga
      - id dو          → update ya delete hoga
    """
    wallpaper_dict = await crud.update_wallpaper(db, payload)
    data = WallpaperResponse(**wallpaper_dict)
    return success_response(data=data, message="Wallpaper updated successfully")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
@router.delete(
    "/{wallpaper_id}",
    summary="Delete a wallpaper and its related themes, icons, widgets",
    response_model=None,
)
async def delete_wallpaper(
    wallpaper_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await crud.delete_wallpaper(db, wallpaper_id)
    return success_response(data=None, message="Wallpaper deleted successfully")
