"""
Database operations ("CRUD" = Create, Read, Update, Delete).

Plain functions that take a DB session and do the work directly — no
repository classes, no service classes, just functions. Routes call
these functions and turn the result into a JSON response.
"""
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Icon, Theme, Wallpaper, Widget
from app.schemas import WallpaperCreateRequest, WallpaperUpdateRequest
from app.utils import get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# Category
# ----------------------------------------------------------------------
def list_categories(db: Session) -> List[Category]:
    stmt = select(Category).order_by(Category.name.asc())
    return list(db.execute(stmt).scalars().all())


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.get(Category, category_id)


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    stmt = select(Category).where(Category.name == name)
    return db.execute(stmt).scalar_one_or_none()


def get_or_create_category(db: Session, name: str) -> Category:
    """Returns the existing category with this name, or creates a new one."""
    existing = get_category_by_name(db, name)
    if existing:
        return existing

    category = Category(name=name)
    db.add(category)
    db.flush()  # assigns category.id without committing the whole transaction
    return category


def find_category_by_id_or_name(db: Session, value: str) -> Category:
    """
    Looks up a category by its numeric id ("3") or by its name ("Nature") —
    whichever the caller passed in. Raises a 404 if nothing matches.
    """
    category: Optional[Category] = None
    if value.isdigit():
        category = get_category_by_id(db, int(value))
    if category is None:
        category = get_category_by_name(db, value)
    if category is None:
        raise HTTPException(status_code=404, detail=f"Category '{value}' not found.")
    return category


# ----------------------------------------------------------------------
# Wallpaper: create
# ----------------------------------------------------------------------
def create_wallpaper(db: Session, payload: WallpaperCreateRequest) -> Wallpaper:
    """
    1. Resolve (get-or-create) category.
    2. Create wallpaper.
    3. Create optional themes/icons/widgets.
    4. Commit transaction (rollback on failure).
    """
    try:
        category = get_or_create_category(db, payload.category_name)

        wallpaper = Wallpaper(
            category_id=category.id,
            title=payload.wallpaper.title,
            home_wallpaper_url=payload.wallpaper.home_wallpaper_url,
            lock_wallpaper_url=payload.wallpaper.lock_wallpaper_url,
        )
        db.add(wallpaper)
        db.flush()  # assigns wallpaper.id so themes/icons/widgets can reference it

        for theme_data in payload.themes or []:
            db.add(
                Theme(
                    wallpaper_id=wallpaper.id,
                    theme_name=theme_data.theme_name,
                    theme_image_url=theme_data.theme_image_url,
                )
            )

        for icon_data in payload.icons or []:
            db.add(
                Icon(
                    wallpaper_id=wallpaper.id,
                    icon_name=icon_data.icon_name,
                    icon_url=icon_data.icon_url,
                )
            )

        for widget_data in payload.widgets or []:
            db.add(
                Widget(
                    wallpaper_id=wallpaper.id,
                    widget_name=widget_data.widget_name,
                    widget_url=widget_data.widget_url,
                )
            )

        db.commit()
        db.refresh(wallpaper)
        logger.info("Created wallpaper %s in category %s", wallpaper.id, category.name)
        return wallpaper

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to create wallpaper")
        raise HTTPException(status_code=500, detail=f"Failed to create wallpaper: {e}")


# ----------------------------------------------------------------------
# Wallpaper: read
# ----------------------------------------------------------------------
def get_wallpaper_or_404(db: Session, wallpaper_id: int) -> Wallpaper:
    wallpaper = db.get(Wallpaper, wallpaper_id)
    if not wallpaper:
        raise HTTPException(status_code=404, detail=f"Wallpaper '{wallpaper_id}' not found.")
    return wallpaper


def list_wallpapers_by_category(
    db: Session, category_id_or_name: str
) -> Tuple[Category, List[Wallpaper]]:
    """
    Returns every wallpaper that belongs to a category — no pagination,
    the caller gets the full list. `category_id_or_name` can be either
    the category's numeric id or its name.
    """
    category = find_category_by_id_or_name(db, category_id_or_name)
    stmt = (
        select(Wallpaper)
        .where(Wallpaper.category_id == category.id)
        .order_by(Wallpaper.created_at.desc())
    )
    items = list(db.execute(stmt).scalars().all())
    return category, items


# ----------------------------------------------------------------------
# Wallpaper: update
# ----------------------------------------------------------------------
def update_wallpaper(
    db: Session, wallpaper_id: int, payload: WallpaperUpdateRequest
) -> Wallpaper:
    """
    Supports: category change, wallpaper field updates, and add/update/delete
    operations for themes, icons, and widgets — all in a single request.
    """
    wallpaper = get_wallpaper_or_404(db, wallpaper_id)

    try:
        if payload.category_name:
            category = get_or_create_category(db, payload.category_name)
            wallpaper.category_id = category.id

        if payload.wallpaper:
            update_data = payload.wallpaper.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(wallpaper, field, value)

        if payload.themes is not None:
            _sync_themes(db, wallpaper.id, payload.themes)

        if payload.icons is not None:
            _sync_icons(db, wallpaper.id, payload.icons)

        if payload.widgets is not None:
            _sync_widgets(db, wallpaper.id, payload.widgets)

        db.commit()
        db.refresh(wallpaper)
        logger.info("Updated wallpaper %s", wallpaper.id)
        return wallpaper

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to update wallpaper %s", wallpaper_id)
        raise HTTPException(status_code=500, detail=f"Failed to update wallpaper: {e}")


def _sync_themes(db: Session, wallpaper_id: int, theme_updates) -> None:
    for item in theme_updates:
        if item.id:
            theme = db.get(Theme, item.id)
            if not theme or theme.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=404, detail=f"Theme '{item.id}' not found on this wallpaper."
                )
            if item.delete:
                db.delete(theme)
                continue
            if item.theme_name is not None:
                theme.theme_name = item.theme_name
            if item.theme_image_url is not None:
                theme.theme_image_url = item.theme_image_url
        else:
            db.add(
                Theme(
                    wallpaper_id=wallpaper_id,
                    theme_name=item.theme_name,
                    theme_image_url=item.theme_image_url,
                )
            )


def _sync_icons(db: Session, wallpaper_id: int, icon_updates) -> None:
    for item in icon_updates:
        if item.id:
            icon = db.get(Icon, item.id)
            if not icon or icon.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=404, detail=f"Icon '{item.id}' not found on this wallpaper."
                )
            if item.delete:
                db.delete(icon)
                continue
            if item.icon_name is not None:
                icon.icon_name = item.icon_name
            if item.icon_url is not None:
                icon.icon_url = item.icon_url
        else:
            db.add(
                Icon(
                    wallpaper_id=wallpaper_id,
                    icon_name=item.icon_name,
                    icon_url=item.icon_url,
                )
            )


def _sync_widgets(db: Session, wallpaper_id: int, widget_updates) -> None:
    for item in widget_updates:
        if item.id:
            widget = db.get(Widget, item.id)
            if not widget or widget.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=404, detail=f"Widget '{item.id}' not found on this wallpaper."
                )
            if item.delete:
                db.delete(widget)
                continue
            if item.widget_name is not None:
                widget.widget_name = item.widget_name
            if item.widget_url is not None:
                widget.widget_url = item.widget_url
        else:
            db.add(
                Widget(
                    wallpaper_id=wallpaper_id,
                    widget_name=item.widget_name,
                    widget_url=item.widget_url,
                )
            )


# ----------------------------------------------------------------------
# Wallpaper: delete
# ----------------------------------------------------------------------
def delete_wallpaper(db: Session, wallpaper_id: int) -> None:
    wallpaper = get_wallpaper_or_404(db, wallpaper_id)
    try:
        db.delete(wallpaper)  # cascade removes its themes/icons/widgets too
        db.commit()
        logger.info("Deleted wallpaper %s", wallpaper_id)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete wallpaper %s", wallpaper_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete wallpaper: {e}")
