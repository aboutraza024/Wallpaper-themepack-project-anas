"""
Database operations — async MongoDB via Motor.

All functions are async and accept an AsyncIOMotorDatabase object.

Key changes:
  • Duplicate category name raises 409
  • Duplicate wallpaper title within same category raises 409
  • Theme/icon/widget incorrect id on PUT raises 400 with specific message
  • delete_category cascades → deletes all wallpapers in that category
  • delete_wallpaper cascades → themes/icons/widgets embedded, auto-removed
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import COL_CATEGORIES, COL_WALLPAPERS
from app.models import is_valid_oid, new_sub_doc, utcnow
from app.schemas import WallpaperCreateRequest, WallpaperUpdateRequest
from app.utils import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _oid(value: str) -> ObjectId:
    """Convert a string to ObjectId, raising 400 if malformed."""
    if not is_valid_oid(value):
        raise HTTPException(status_code=400, detail=f"'{value}' is not a valid id.")
    return ObjectId(value)


def _cat_to_dict(doc: dict) -> dict:
    """Normalise a category document: rename _id → id as string."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def _sub_to_dict(sub: dict, wallpaper_id: str) -> dict:
    """Normalise an embedded sub-document: rename _id → id, inject wallpaper_id."""
    return {**sub, "id": str(sub["_id"]), "wallpaper_id": wallpaper_id}


def _wallpaper_to_dict(doc: dict, category_doc: dict) -> dict:
    """
    Build a fully-hydrated wallpaper dict ready to be validated by
    WallpaperResponse.  Converts all ObjectIds to strings.
    """
    wid = str(doc["_id"])
    return {
        "id": wid,
        "title": doc["title"],
        "home_wallpaper_url": doc["home_wallpaper_url"],
        "lock_wallpaper_url": doc["lock_wallpaper_url"],
        "category": _cat_to_dict(category_doc),
        "themes": [_sub_to_dict(t, wid) for t in doc.get("themes", [])],
        "icons": [_sub_to_dict(i, wid) for i in doc.get("icons", [])],
        "widgets": [_sub_to_dict(w, wid) for w in doc.get("widgets", [])],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


# Map array field names to human-readable singular labels for error messages
_ARRAY_FIELD_LABEL = {
    "themes": "theme",
    "icons": "icon",
    "widgets": "widget",
}


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

async def list_categories(db: AsyncIOMotorDatabase) -> List[dict]:
    cursor = db[COL_CATEGORIES].find().sort("name", 1)
    return [_cat_to_dict(doc) async for doc in cursor]


async def get_category_by_id(
    db: AsyncIOMotorDatabase, category_id: str
) -> Optional[dict]:
    doc = await db[COL_CATEGORIES].find_one({"_id": _oid(category_id)})
    return _cat_to_dict(doc) if doc else None


async def get_category_by_name(
    db: AsyncIOMotorDatabase, name: str
) -> Optional[dict]:
    doc = await db[COL_CATEGORIES].find_one({"name": name})
    return _cat_to_dict(doc) if doc else None


async def create_category(db: AsyncIOMotorDatabase, name: str) -> dict:
    """
    Explicitly create a new category.
    Raises 409 if a category with the same name already exists.
    """
    existing = await get_category_by_name(db, name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Category with name '{name}' already exists.",
        )

    now = utcnow()
    result = await db[COL_CATEGORIES].insert_one(
        {"name": name, "created_at": now, "updated_at": now}
    )
    doc = await db[COL_CATEGORIES].find_one({"_id": result.inserted_id})
    logger.info("Created category '%s'", name)
    return _cat_to_dict(doc)


async def get_or_create_category(db: AsyncIOMotorDatabase, name: str) -> dict:
    """
    Return the existing category with this name, or create a new one.
    Used internally by create_wallpaper so a wallpaper can be created
    with a brand-new category name in a single request.
    """
    existing = await get_category_by_name(db, name)
    if existing:
        return existing

    now = utcnow()
    result = await db[COL_CATEGORIES].insert_one(
        {"name": name, "created_at": now, "updated_at": now}
    )
    doc = await db[COL_CATEGORIES].find_one({"_id": result.inserted_id})
    logger.info("Created category '%s'", name)
    return _cat_to_dict(doc)


async def find_category_by_id_or_name(
    db: AsyncIOMotorDatabase, value: str
) -> dict:
    """
    Looks up a category by ObjectId string or by name.
    Raises 404 if nothing matches.
    """
    category: Optional[dict] = None
    if is_valid_oid(value):
        category = await get_category_by_id(db, value)
    if category is None:
        category = await get_category_by_name(db, value)
    if category is None:
        raise HTTPException(status_code=404, detail=f"Category '{value}' not found.")
    return category


async def delete_category(db: AsyncIOMotorDatabase, category_id: str) -> int:
    """
    Delete a category and ALL wallpapers that belong to it (cascade delete).
    Returns the count of wallpapers deleted.
    Raises 404 if the category does not exist.
    """
    cat_doc = await db[COL_CATEGORIES].find_one({"_id": _oid(category_id)})
    if not cat_doc:
        raise HTTPException(
            status_code=404, detail=f"Category '{category_id}' not found."
        )

    cat_oid = cat_doc["_id"]

    try:
        # 1. Delete every wallpaper in this category (themes/icons/widgets are
        #    embedded, so they are automatically removed with the wallpaper doc)
        result = await db[COL_WALLPAPERS].delete_many({"category_id": cat_oid})
        deleted_wallpapers = result.deleted_count

        # 2. Delete the category itself
        await db[COL_CATEGORIES].delete_one({"_id": cat_oid})

        logger.info(
            "Deleted category '%s' and %d wallpaper(s)",
            cat_doc["name"],
            deleted_wallpapers,
        )
        return deleted_wallpapers

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete category %s", category_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete category: {e}"
        )


# ---------------------------------------------------------------------------
# Wallpaper: create
# ---------------------------------------------------------------------------

async def create_wallpaper(
    db: AsyncIOMotorDatabase, payload: WallpaperCreateRequest
) -> dict:
    """
    1. Resolve (get-or-create) category.
    2. Check for duplicate wallpaper title within the same category → 409.
    3. Build the wallpaper document with embedded themes / icons / widgets.
    4. Insert in a single write.
    """
    try:
        category = await get_or_create_category(db, payload.category_name)
        cat_oid = ObjectId(category["id"])

        # ── duplicate title guard ──────────────────────────────────────
        existing_wp = await db[COL_WALLPAPERS].find_one(
            {"category_id": cat_oid, "title": payload.wallpaper.title}
        )
        if existing_wp:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A wallpaper with title '{payload.wallpaper.title}' already "
                    f"exists in category '{category['name']}'."
                ),
            )

        now = utcnow()

        themes = [
            new_sub_doc({"theme_name": t.theme_name, "theme_image_url": t.theme_image_url})
            for t in (payload.themes or [])
        ]
        icons = [
            new_sub_doc({"icon_name": i.icon_name, "icon_url": i.icon_url})
            for i in (payload.icons or [])
        ]
        widgets = [
            new_sub_doc({"widget_name": w.widget_name, "widget_url": w.widget_url})
            for w in (payload.widgets or [])
        ]

        doc = {
            "category_id": cat_oid,
            "title": payload.wallpaper.title,
            "home_wallpaper_url": payload.wallpaper.home_wallpaper_url,
            "lock_wallpaper_url": payload.wallpaper.lock_wallpaper_url,
            "themes": themes,
            "icons": icons,
            "widgets": widgets,
            "created_at": now,
            "updated_at": now,
        }

        result = await db[COL_WALLPAPERS].insert_one(doc)
        inserted = await db[COL_WALLPAPERS].find_one({"_id": result.inserted_id})
        logger.info("Created wallpaper %s in category '%s'", result.inserted_id, category["name"])
        cat_doc = await db[COL_CATEGORIES].find_one({"_id": cat_oid})
        return _wallpaper_to_dict(inserted, cat_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create wallpaper")
        raise HTTPException(status_code=500, detail=f"Failed to create wallpaper: {e}")


# ---------------------------------------------------------------------------
# Wallpaper: read
# ---------------------------------------------------------------------------

async def get_wallpaper_or_404(
    db: AsyncIOMotorDatabase, wallpaper_id: str
) -> dict:
    doc = await db[COL_WALLPAPERS].find_one({"_id": _oid(wallpaper_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Wallpaper '{wallpaper_id}' not found.")
    cat_doc = await db[COL_CATEGORIES].find_one({"_id": doc["category_id"]})
    return _wallpaper_to_dict(doc, cat_doc)


async def list_wallpapers_by_category(
    db: AsyncIOMotorDatabase, category_id_or_name: str
) -> Tuple[dict, List[dict]]:
    """
    Returns (category_dict, list_of_wallpaper_dicts) for a given category.
    `category_id_or_name` can be either the ObjectId string or the category name.
    """
    category = await find_category_by_id_or_name(db, category_id_or_name)
    cat_oid = ObjectId(category["id"])
    cat_doc = await db[COL_CATEGORIES].find_one({"_id": cat_oid})

    cursor = (
        db[COL_WALLPAPERS]
        .find({"category_id": cat_oid})
        .sort("created_at", -1)
    )
    items = [_wallpaper_to_dict(doc, cat_doc) async for doc in cursor]
    return category, items


# ---------------------------------------------------------------------------
# Wallpaper: update
# ---------------------------------------------------------------------------

async def update_wallpaper(
    db: AsyncIOMotorDatabase, payload: WallpaperUpdateRequest
) -> dict:
    """
    wallpaper_id payload body se aata hai — URL parameter nahi.

    Partial update rules:
      - category_name diya  → category update hogi
      - title diya          → title update hoga
      - home/lock_url diya  → url update hogi
      - koi field None/empty → woh field nahi badlegi
      - themes/icons/widgets:
          id omit  → ADD
          id given → UPDATE ya DELETE (id galat ho to 400 error)
    """
    wallpaper_id = payload.wallpaper_id

    # Verify the wallpaper exists first
    doc = await db[COL_WALLPAPERS].find_one({"_id": _oid(wallpaper_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Wallpaper '{wallpaper_id}' not found.")

    try:
        set_fields: dict = {"updated_at": utcnow()}

        # ── category change ────────────────────────────────────────────
        if payload.category_name is not None:
            category = await get_or_create_category(db, payload.category_name)
            set_fields["category_id"] = ObjectId(category["id"])

        # ── core wallpaper fields (sirf jo bheja woh update hoga) ──────
        if payload.title is not None:
            set_fields["title"] = payload.title
        if payload.home_wallpaper_url is not None:
            set_fields["home_wallpaper_url"] = payload.home_wallpaper_url
        if payload.lock_wallpaper_url is not None:
            set_fields["lock_wallpaper_url"] = payload.lock_wallpaper_url

        await db[COL_WALLPAPERS].update_one(
            {"_id": _oid(wallpaper_id)}, {"$set": set_fields}
        )

        # ── themes / icons / widgets ───────────────────────────────────
        if payload.themes is not None:
            await _sync_sub_docs(
                db, wallpaper_id, "themes", payload.themes,
                name_key="theme_name",
                extra_keys=["theme_image_url"],
            )

        if payload.icons is not None:
            await _sync_sub_docs(
                db, wallpaper_id, "icons", payload.icons,
                name_key="icon_name",
                extra_keys=["icon_url"],
            )

        if payload.widgets is not None:
            await _sync_sub_docs(
                db, wallpaper_id, "widgets", payload.widgets,
                name_key="widget_name",
                extra_keys=["widget_url"],
            )

        logger.info("Updated wallpaper %s", wallpaper_id)
        return await get_wallpaper_or_404(db, wallpaper_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update wallpaper %s", wallpaper_id)
        raise HTTPException(status_code=500, detail=f"Failed to update wallpaper: {e}")


async def _sync_sub_docs(
    db: AsyncIOMotorDatabase,
    wallpaper_id: str,
    array_field: str,
    updates: list,
    *,
    name_key: str,
    extra_keys: List[str],
) -> None:
    """
    Process a list of ThemeUpdate / IconUpdate / WidgetUpdate items:

      • item.id is None  → $push a new sub-document  (no id required)
      • item.id set, delete=True  → validate id exists, then $pull
      • item.id set, delete=False → validate id exists, then $set via arrayFilters

    Raises 400 with "Incorrect id of <theme|icon|widget>" if the provided
    id does not match any sub-document in the wallpaper's array.
    """
    label = _ARRAY_FIELD_LABEL.get(array_field, array_field.rstrip("s"))

    for item in updates:
        item_dict = item.model_dump(exclude_unset=True)

        if item.id is None:
            # ── ADD new sub-document (id not required) ─────────────────
            sub = {name_key: item_dict.get(name_key)}
            for k in extra_keys:
                sub[k] = item_dict.get(k)
            await db[COL_WALLPAPERS].update_one(
                {"_id": _oid(wallpaper_id)},
                {"$push": {array_field: new_sub_doc(sub)}},
            )
        else:
            sub_oid = _oid(item.id)

            # ── Validate the sub-document id exists ────────────────────
            parent = await db[COL_WALLPAPERS].find_one(
                {"_id": _oid(wallpaper_id), f"{array_field}._id": sub_oid}
            )
            if not parent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect id of {label}: '{item.id}' not found.",
                )

            if item.delete:
                # ── DELETE sub-document ────────────────────────────────
                await db[COL_WALLPAPERS].update_one(
                    {"_id": _oid(wallpaper_id)},
                    {"$pull": {array_field: {"_id": sub_oid}}},
                )
            else:
                # ── UPDATE sub-document ────────────────────────────────
                set_payload: dict = {f"{array_field}.$[elem].updated_at": utcnow()}
                if name_key in item_dict and item_dict[name_key] is not None:
                    set_payload[f"{array_field}.$[elem].{name_key}"] = item_dict[name_key]
                for k in extra_keys:
                    if k in item_dict and item_dict[k] is not None:
                        set_payload[f"{array_field}.$[elem].{k}"] = item_dict[k]

                await db[COL_WALLPAPERS].update_one(
                    {"_id": _oid(wallpaper_id)},
                    {"$set": set_payload},
                    array_filters=[{"elem._id": sub_oid}],
                )


# ---------------------------------------------------------------------------
# Wallpaper: delete
# ---------------------------------------------------------------------------

async def delete_wallpaper(db: AsyncIOMotorDatabase, wallpaper_id: str) -> None:
    """
    Delete a wallpaper document.
    All embedded themes, icons, and widgets are stored inside the wallpaper
    document and are therefore automatically removed when the document is deleted.
    """
    doc = await db[COL_WALLPAPERS].find_one({"_id": _oid(wallpaper_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Wallpaper '{wallpaper_id}' not found.")
    try:
        await db[COL_WALLPAPERS].delete_one({"_id": _oid(wallpaper_id)})
        logger.info("Deleted wallpaper %s (themes/icons/widgets removed with it)", wallpaper_id)
    except Exception as e:
        logger.exception("Failed to delete wallpaper %s", wallpaper_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete wallpaper: {e}")
