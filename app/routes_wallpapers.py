"""API routes for Wallpaper resources (create, read, update, delete, upload)."""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

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


# --------------------------------------------------------------------------
# File Upload Endpoint (Option 1: direct file upload -> S3 mock -> URL)
# --------------------------------------------------------------------------
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
    Uploads a single file (home/lock wallpaper, theme, icon, or widget image)
    and returns the resulting URL. The returned URL can then be passed into
    the create/update wallpaper payloads as the corresponding `*_url` field.
    """
    folder = S3_UPLOAD_FOLDERS.get(asset_type, "uploads")
    url = await s3_service.upload_file(file, folder=folder)
    data = UploadResponse(url=url, filename=file.filename)
    return success_response(data=data, message="File uploaded successfully")


# --------------------------------------------------------------------------
# Create
# --------------------------------------------------------------------------
@router.post(
    "",
    summary="Create a wallpaper (with optional themes, icons, widgets)",
    response_model=None,
    status_code=201,
)
def create_wallpaper(
    payload: WallpaperCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Creates a wallpaper. If the given category name already exists it is
    reused; otherwise a new category is created automatically. Themes,
    icons, and widgets are optional and may be fully omitted.
    """
    wallpaper = crud.create_wallpaper(db, payload)
    data = WallpaperResponse.model_validate(wallpaper)
    return success_response(data=data, message="Wallpaper created successfully")


# --------------------------------------------------------------------------
# Get details
# --------------------------------------------------------------------------
@router.get(
    "/{wallpaper_id}",
    summary="Get full wallpaper details (with nested themes, icons, widgets)",
    response_model=None,
)
def get_wallpaper(
    wallpaper_id: int,
    db: Session = Depends(get_db),
):
    wallpaper = crud.get_wallpaper_or_404(db, wallpaper_id)
    data = WallpaperResponse.model_validate(wallpaper)
    return success_response(data=data, message="Wallpaper fetched successfully")


# --------------------------------------------------------------------------
# Update (PATCH-like partial update via PUT)
# --------------------------------------------------------------------------
@router.put(
    "/{wallpaper_id}",
    summary="Update a wallpaper (supports partial/PATCH-like updates)",
    response_model=None,
)
def update_wallpaper(
    wallpaper_id: int,
    payload: WallpaperUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Supports: category change, wallpaper field updates, and add/update/delete
    operations for themes, icons, and widgets — all in a single request.
    """
    wallpaper = crud.update_wallpaper(db, wallpaper_id, payload)
    data = WallpaperResponse.model_validate(wallpaper)
    return success_response(data=data, message="Wallpaper updated successfully")


# --------------------------------------------------------------------------
# Delete
# --------------------------------------------------------------------------
@router.delete(
    "/{wallpaper_id}",
    summary="Delete a wallpaper and its related themes, icons, widgets",
    response_model=None,
)
def delete_wallpaper(
    wallpaper_id: int,
    db: Session = Depends(get_db),
):
    crud.delete_wallpaper(db, wallpaper_id)
    return success_response(data=None, message="Wallpaper deleted successfully")
