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
# Internal helpers — duplicate name validation
# ----------------------------------------------------------------------

def _check_duplicate_names_in_list(names: List[str], field_label: str) -> None:
    """
    CREATE ke waqt: ek hi request mein bheje gaye items ka name unique hona chahiye.
    Example: 2 themes ka naam 'Dark Mode' nahi ho sakta.
    """
    seen = set()
    for name in names:
        lower = name.lower()
        if lower in seen:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate {field_label}_name in request: '{name}'. Har {field_label} ka naam alag hona chahiye.",
            )
        seen.add(lower)


def _compute_final_names_themes(
    db: Session,
    wallpaper_id: int,
    theme_updates: list,
) -> None:
    """
    UPDATE ke waqt themes ka final state simulate karo aur check karo:
      - koi 2 themes ka naam same nah ho
      - agar koi item apna hi naam rakh raha hai to woh OK hai
    """
    # Load existing themes
    existing = list(
        db.execute(select(Theme).where(Theme.wallpaper_id == wallpaper_id)).scalars()
    )
    # id → name map (jo abhi DB mein hai)
    final: dict[int, str] = {t.id: t.theme_name for t in existing}

    # Simulate all update operations
    for item in theme_updates:
        if item.id:
            if item.id not in final:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of theme: '{item.id}' not found.",
                )
            if item.delete:
                del final[item.id]
            elif item.theme_name is not None:
                final[item.id] = item.theme_name
        else:
            # New item — use a temporary negative key
            temp_key = -(len(final) + 1)
            while temp_key in final:
                temp_key -= 1
            final[temp_key] = item.theme_name

    # Check for duplicates in final state
    seen: dict[str, int] = {}
    for k, name in final.items():
        lower = name.lower()
        if lower in seen:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate theme_name: '{name}'. Is wallpaper mein yeh naam pehle se maujood hai.",
            )
        seen[lower] = k


def _compute_final_names_icons(
    db: Session,
    wallpaper_id: int,
    icon_updates: list,
) -> None:
    existing = list(
        db.execute(select(Icon).where(Icon.wallpaper_id == wallpaper_id)).scalars()
    )
    final: dict[int, str] = {i.id: i.icon_name for i in existing}

    for item in icon_updates:
        if item.id:
            if item.id not in final:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of icon: '{item.id}' not found.",
                )
            if item.delete:
                del final[item.id]
            elif item.icon_name is not None:
                final[item.id] = item.icon_name
        else:
            temp_key = -(len(final) + 1)
            while temp_key in final:
                temp_key -= 1
            final[temp_key] = item.icon_name

    seen: dict[str, int] = {}
    for k, name in final.items():
        lower = name.lower()
        if lower in seen:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate icon_name: '{name}'. Is wallpaper mein yeh naam pehle se maujood hai.",
            )
        seen[lower] = k


def _compute_final_names_widgets(
    db: Session,
    wallpaper_id: int,
    widget_updates: list,
) -> None:
    existing = list(
        db.execute(select(Widget).where(Widget.wallpaper_id == wallpaper_id)).scalars()
    )
    final: dict[int, str] = {w.id: w.widget_name for w in existing}

    for item in widget_updates:
        if item.id:
            if item.id not in final:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of widget: '{item.id}' not found.",
                )
            if item.delete:
                del final[item.id]
            elif item.widget_name is not None:
                final[item.id] = item.widget_name
        else:
            temp_key = -(len(final) + 1)
            while temp_key in final:
                temp_key -= 1
            final[temp_key] = item.widget_name

    seen: dict[str, int] = {}
    for k, name in final.items():
        lower = name.lower()
        if lower in seen:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate widget_name: '{name}'. Is wallpaper mein yeh naam pehle se maujood hai.",
            )
        seen[lower] = k


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


def create_category(db: Session, name: str) -> Category:
    """
    Explicitly create a new category.
    Raises 409 if a category with the same name already exists.
    """
    existing = get_category_by_name(db, name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Category with name '{name}' already exists.",
        )
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    logger.info("Created category '%s'", name)
    return category


def get_or_create_category(db: Session, name: str) -> Category:
    """Returns the existing category with this name, or creates a new one."""
    existing = get_category_by_name(db, name)
    if existing:
        return existing
    category = Category(name=name)
    db.add(category)
    db.flush()
    logger.info("Created category '%s'", name)
    return category


def find_category_by_id_or_name(db: Session, value: str) -> Category:
    """
    Looks up a category by its numeric id ("3") or by its name ("Nature").
    Raises a 404 if nothing matches.
    """
    category: Optional[Category] = None
    if value.isdigit():
        category = get_category_by_id(db, int(value))
    if category is None:
        category = get_category_by_name(db, value)
    if category is None:
        raise HTTPException(status_code=404, detail=f"Category '{value}' not found.")
    return category


def delete_category(db: Session, category_id: int) -> int:
    """
    Delete a category and ALL wallpapers that belong to it (cascade delete).
    Returns the count of wallpapers deleted.
    Raises 404 if the category does not exist.
    """
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Category '{category_id}' not found."
        )
    try:
        stmt = select(Wallpaper).where(Wallpaper.category_id == category_id)
        wallpapers = list(db.execute(stmt).scalars().all())
        deleted_wallpapers = len(wallpapers)

        db.delete(category)  # cascade removes all wallpapers + their themes/icons/widgets
        db.commit()

        logger.info(
            "Deleted category '%s' and %d wallpaper(s)",
            category.name,
            deleted_wallpapers,
        )
        return deleted_wallpapers

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to delete category %s", category_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete category: {e}"
        )


# ----------------------------------------------------------------------
# Wallpaper: create
# ----------------------------------------------------------------------
def create_wallpaper(db: Session, payload: WallpaperCreateRequest) -> Wallpaper:
    """
    1. Resolve (get-or-create) category.
    2. Check for duplicate wallpaper title within the same category → 409.
    3. Check for duplicate names within themes / icons / widgets → 409.
    4. Create wallpaper with embedded items.
    5. Commit transaction (rollback on failure).
    """
    try:
        category = get_or_create_category(db, payload.category_name)

        # ── duplicate wallpaper title guard ───────────────────────────
        existing_wp = db.execute(
            select(Wallpaper).where(
                Wallpaper.category_id == category.id,
                Wallpaper.title == payload.wallpaper.title,
            )
        ).scalar_one_or_none()
        if existing_wp:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A wallpaper with title '{payload.wallpaper.title}' already "
                    f"exists in category '{category.name}'."
                ),
            )

        # ── duplicate name guard within request payload ────────────────
        _check_duplicate_names_in_list(
            [t.theme_name for t in (payload.themes or [])], "theme"
        )
        _check_duplicate_names_in_list(
            [i.icon_name for i in (payload.icons or [])], "icon"
        )
        _check_duplicate_names_in_list(
            [w.widget_name for w in (payload.widgets or [])], "widget"
        )

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
    Returns every wallpaper that belongs to a category.
    `category_id_or_name` can be either the category's numeric id or its name.
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
def update_wallpaper(db: Session, payload: WallpaperUpdateRequest) -> Wallpaper:
    """
    wallpaper_id payload body se aata hai — URL parameter nahi.

    Duplicate name rule:
      - koi 2 themes/icons/widgets ka naam same nah ho sakta (case-insensitive)
      - agar existing item apna hi naam rakh raha hai to koi masla nahi
    """
    wallpaper = get_wallpaper_or_404(db, payload.wallpaper_id)

    try:
        # ── simulate final state and validate BEFORE making any changes ──
        if payload.themes is not None:
            _compute_final_names_themes(db, wallpaper.id, payload.themes)
        if payload.icons is not None:
            _compute_final_names_icons(db, wallpaper.id, payload.icons)
        if payload.widgets is not None:
            _compute_final_names_widgets(db, wallpaper.id, payload.widgets)

        # ── apply changes ───────────────────────────────────────────────
        if payload.category_name is not None:
            category = get_or_create_category(db, payload.category_name)
            wallpaper.category_id = category.id

        if payload.title is not None:
            wallpaper.title = payload.title
        if payload.home_wallpaper_url is not None:
            wallpaper.home_wallpaper_url = payload.home_wallpaper_url
        if payload.lock_wallpaper_url is not None:
            wallpaper.lock_wallpaper_url = payload.lock_wallpaper_url

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
        logger.exception("Failed to update wallpaper %s", payload.wallpaper_id)
        raise HTTPException(status_code=500, detail=f"Failed to update wallpaper: {e}")


def _sync_themes(db: Session, wallpaper_id: int, theme_updates) -> None:
    """Apply theme add / update / delete operations (validation already done)."""
    for item in theme_updates:
        if item.id:
            theme = db.get(Theme, item.id)
            if not theme or theme.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of theme: '{item.id}' not found.",
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
    """Apply icon add / update / delete operations (validation already done)."""
    for item in icon_updates:
        if item.id:
            icon = db.get(Icon, item.id)
            if not icon or icon.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of icon: '{item.id}' not found.",
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
    """Apply widget add / update / delete operations (validation already done)."""
    for item in widget_updates:
        if item.id:
            widget = db.get(Widget, item.id)
            if not widget or widget.wallpaper_id != wallpaper_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of widget: '{item.id}' not found.",
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
