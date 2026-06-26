"""
MongoDB document helpers.

We no longer use SQLAlchemy ORM classes.  Instead, MongoDB documents are
plain Python dicts.  This module provides:

  • utcnow()        — timezone-aware UTC datetime for created_at / updated_at
  • is_valid_oid()  — check whether a string is a well-formed ObjectId
  • new_sub_doc()   — build a fresh embedded sub-document (theme / icon / widget)
    with its own _id, so it can be targeted by array-filter updates later.

The structure stored in MongoDB is:

  categories  collection
  ─────────────────────────────────────────────────
  {
    _id:        ObjectId,
    name:       str  (unique, indexed),
    created_at: datetime,
    updated_at: datetime,
  }

  wallpapers  collection
  ─────────────────────────────────────────────────
  {
    _id:               ObjectId,
    category_id:       ObjectId  (ref → categories._id, indexed),
    title:             str,
    home_wallpaper_url: str,
    lock_wallpaper_url: str,
    created_at:        datetime,
    updated_at:        datetime,
    themes:  [ { _id, theme_name, theme_image_url,  created_at, updated_at } ],
    icons:   [ { _id, icon_name,  icon_url,          created_at, updated_at } ],
    widgets: [ { _id, widget_name, widget_url,        created_at, updated_at } ],
  }

Themes / icons / widgets are embedded inside the wallpaper document because:
  • They are always fetched together with the wallpaper (no N+1 queries).
  • Deleting a wallpaper automatically removes its children.
  • The total size of a wallpaper document stays well within MongoDB's 16 MB limit.
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


def utcnow() -> datetime:
    """Current UTC time — stored as a UTC-aware datetime in MongoDB."""
    return datetime.now(timezone.utc)


def is_valid_oid(value: str) -> bool:
    """Return True if *value* is a valid 24-hex-char ObjectId string."""
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


def new_sub_doc(data: dict) -> dict:
    """
    Wrap *data* in a fresh sub-document with its own _id and timestamps.
    Use this when appending a new theme / icon / widget to a wallpaper.
    """
    now = utcnow()
    return {
        "_id": ObjectId(),
        **data,
        "created_at": now,
        "updated_at": now,
    }
