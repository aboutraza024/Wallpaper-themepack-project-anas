"""API routes for Category resources."""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import crud
from app.database import get_db
from app.schemas import CategoryCreate, CategoryResponse, WallpaperListItemResponse
from app.utils import success_response

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    summary="List all categories",
    response_model=None,
)
async def list_categories(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Returns all wallpaper categories sorted by name."""
    categories = await crud.list_categories(db)
    data = [CategoryResponse(**c) for c in categories]
    return success_response(data=data, message="Categories fetched successfully")


@router.post(
    "",
    summary="Create a new category",
    response_model=None,
    status_code=201,
)
async def create_category(
    payload: CategoryCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Creates a new category.
    Returns 409 Conflict if a category with the same name already exists.
    """
    category = await crud.create_category(db, payload.name)
    data = CategoryResponse(**category)
    return success_response(data=data, message="Category created successfully")


@router.get(
    "/{category}/wallpapers",
    summary="Get all wallpapers in a category (by ObjectId string or by name)",
    response_model=None,
)
async def get_wallpapers_by_category(
    category: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Returns every wallpaper that belongs to a category.

    `category` can be either:
      - the category's ObjectId string  e.g. /categories/664f1a2b3c4d5e6f7a8b9c0d/wallpapers
      - the category's name             e.g. /categories/Nature/wallpapers
    """
    category_obj, items = await crud.list_wallpapers_by_category(db, category)
    data = [WallpaperListItemResponse(**item) for item in items]
    return success_response(
        data=data,
        message=f"Wallpapers for category '{category_obj['name']}' fetched successfully",
    )


@router.delete(
    "/{category_id}",
    summary="Delete a category and ALL its wallpapers (cascade delete)",
    response_model=None,
)
async def delete_category(
    category_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Permanently deletes the category identified by `category_id`.

    **Cascade behaviour:**
    Every wallpaper that belongs to this category is also deleted, along with
    all themes, icons, and widgets embedded inside those wallpapers.

    Returns 404 if the category does not exist.
    """
    deleted_wallpapers = await crud.delete_category(db, category_id)
    return success_response(
        data={"deleted_wallpapers": deleted_wallpapers},
        message=(
            f"Category deleted successfully along with "
            f"{deleted_wallpapers} wallpaper(s)."
        ),
    )
