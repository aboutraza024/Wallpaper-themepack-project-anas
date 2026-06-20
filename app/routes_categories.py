"""API routes for Category resources."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import CategoryResponse, WallpaperListItemResponse
from app.utils import success_response

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    summary="List all categories",
    response_model=None,
)
def list_categories(db: Session = Depends(get_db)):
    """Returns all wallpaper categories."""
    categories = crud.list_categories(db)
    data = [CategoryResponse.model_validate(c) for c in categories]
    return success_response(data=data, message="Categories fetched successfully")


@router.get(
    "/{category}/wallpapers",
    summary="Get all wallpapers in a category (by id or by name)",
    response_model=None,
)
def get_wallpapers_by_category(category: str, db: Session = Depends(get_db)):
    """
    Returns every wallpaper that belongs to a category — no pagination,
    you get the full list in one response.

    `category` can be either:
      - the category's numeric id, e.g. `/categories/3/wallpapers`
      - the category's name, e.g. `/categories/Nature/wallpapers`
    """
    category_obj, items = crud.list_wallpapers_by_category(db, category)
    data = [WallpaperListItemResponse.model_validate(item) for item in items]
    return success_response(
        data=data,
        message=f"Wallpapers for category '{category_obj.name}' fetched successfully",
    )
