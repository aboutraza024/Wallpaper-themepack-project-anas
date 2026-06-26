"""
Pydantic schemas — define the shape of API request and response data.

Changes from the MySQL version:
  • All `id` fields are now `str` (the string form of a MongoDB ObjectId).
  • `wallpaper_id` in sub-document responses is also `str`.
  • Response schemas no longer use `from_attributes=True` because we build
    them from plain dicts (not ORM objects).  A helper `from_mongo()` is
    used in routes instead.
  • Everything else — validators, envelope, nested structure — is identical.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_url(value: str) -> str:
    if not (value.startswith("http://") or value.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")
    return value


def _validate_url_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return _validate_url(value)


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
class ThemeBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "theme_name": "Dark Mode",
                "theme_image_url": "https://cdn.example.com/themes/dark.jpg",
            }
        }
    )

    theme_name: str = Field(..., min_length=1, max_length=255)
    theme_image_url: Optional[str] = Field(default=None, max_length=1024)

    @field_validator("theme_image_url", mode="before")
    @classmethod
    def validate_theme_image_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class ThemeCreate(ThemeBase):
    pass


class ThemeUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "664f1a2b3c4d5e6f7a8b9c0d",
                "theme_name": "Light Mode",
                "theme_image_url": "https://cdn.example.com/themes/light.jpg",
                "delete": False,
            }
        }
    )

    id: Optional[str] = Field(
        default=None, description="Existing theme ObjectId string. Omit to add a new theme."
    )
    theme_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    theme_image_url: Optional[str] = Field(default=None, max_length=1024)
    delete: bool = Field(
        default=False,
        description="Set true to delete this theme during an update operation.",
    )

    @field_validator("theme_image_url", mode="before")
    @classmethod
    def validate_theme_image_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class ThemeResponse(ThemeBase):
    id: str
    wallpaper_id: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Icon
# ---------------------------------------------------------------------------
class IconBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "icon_name": "Settings",
                "icon_url": "https://cdn.example.com/icons/settings.png",
            }
        }
    )

    icon_name: str = Field(..., min_length=1, max_length=255)
    icon_url: Optional[str] = Field(default=None, max_length=1024)

    @field_validator("icon_url", mode="before")
    @classmethod
    def validate_icon_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class IconCreate(IconBase):
    pass


class IconUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "664f1a2b3c4d5e6f7a8b9c0d",
                "icon_name": "Home",
                "icon_url": "https://cdn.example.com/icons/home.png",
                "delete": False,
            }
        }
    )

    id: Optional[str] = Field(
        default=None, description="Existing icon ObjectId string. Omit to add a new icon."
    )
    icon_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    icon_url: Optional[str] = Field(default=None, max_length=1024)
    delete: bool = Field(
        default=False,
        description="Set true to delete this icon during an update operation.",
    )

    @field_validator("icon_url", mode="before")
    @classmethod
    def validate_icon_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class IconResponse(IconBase):
    id: str
    wallpaper_id: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------
class WidgetBase(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "widget_name": "Clock",
                "widget_url": "https://cdn.example.com/widgets/clock.png",
            }
        }
    )

    widget_name: str = Field(..., min_length=1, max_length=255)
    widget_url: Optional[str] = Field(default=None, max_length=1024)

    @field_validator("widget_url", mode="before")
    @classmethod
    def validate_widget_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class WidgetCreate(WidgetBase):
    pass


class WidgetUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "664f1a2b3c4d5e6f7a8b9c0d",
                "widget_name": "Weather",
                "widget_url": "https://cdn.example.com/widgets/weather.png",
                "delete": False,
            }
        }
    )

    id: Optional[str] = Field(
        default=None, description="Existing widget ObjectId string. Omit to add a new widget."
    )
    widget_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    widget_url: Optional[str] = Field(default=None, max_length=1024)
    delete: bool = Field(
        default=False,
        description="Set true to delete this widget during an update operation.",
    )

    @field_validator("widget_url", mode="before")
    @classmethod
    def validate_widget_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_url_optional(value)


class WidgetResponse(WidgetBase):
    id: str
    wallpaper_id: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Wallpaper core fields
# ---------------------------------------------------------------------------
class WallpaperCore(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Forest Pack",
                "home_wallpaper_url": "https://cdn.example.com/wallpapers/home.jpg",
                "lock_wallpaper_url": "https://cdn.example.com/wallpapers/lock.jpg",
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=255)
    home_wallpaper_url: str = Field(..., max_length=1024)
    lock_wallpaper_url: str = Field(..., max_length=1024)

    @field_validator("home_wallpaper_url", "lock_wallpaper_url")
    @classmethod
    def validate_url_format(cls, value: str) -> str:
        return _validate_url(value)





# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
class WallpaperCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_name": "Nature",
                "wallpaper": {
                    "title": "Forest Pack",
                    "home_wallpaper_url": "https://cdn.example.com/wallpapers/home.jpg",
                    "lock_wallpaper_url": "https://cdn.example.com/wallpapers/lock.jpg",
                },
                "themes": [
                    {
                        "theme_name": "Dark Mode",
                        "theme_image_url": "https://cdn.example.com/themes/dark.jpg",
                    }
                ],
                "icons": [
                    {
                        "icon_name": "Settings",
                        "icon_url": "https://cdn.example.com/icons/settings.png",
                    }
                ],
                "widgets": [
                    {
                        "widget_name": "Clock",
                        "widget_url": "https://cdn.example.com/widgets/clock.png",
                    }
                ],
            }
        }
    )

    category_name: str = Field(..., min_length=1, max_length=150)
    wallpaper: WallpaperCore
    themes: Optional[List[ThemeCreate]] = Field(default=None)
    icons: Optional[List[IconCreate]] = Field(default=None)
    widgets: Optional[List[WidgetCreate]] = Field(default=None)


# ---------------------------------------------------------------------------
# Update (PATCH-like partial update via PUT)
# ---------------------------------------------------------------------------
class WallpaperUpdateRequest(BaseModel):
    """
    PUT /wallpapers  — wallpaper_id body mein dena zaroori hai.

    Baaki sab fields optional hain:
      - jo field doge woh update hogi, jo empty rakho woh nahi badlegi.
      - category_name doge to category update hogi, nahi doge to nahi badlegi.
      - title / home_wallpaper_url / lock_wallpaper_url same rule follow karte hain.

    Themes / icons / widgets entries:
      - id omit karo  → naya ADD ho ga
      - id do          → UPDATE ya DELETE ho ga existing sub-document
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wallpaper_id": "664f1a2b3c4d5e6f7a8b9c0d",
                "category_name": "Nature",
                "title": "Updated Forest Pack",
                "home_wallpaper_url": "https://cdn.example.com/wallpapers/home_new.jpg",
                "lock_wallpaper_url": "https://cdn.example.com/wallpapers/lock_new.jpg",
                "themes": [
                    {
                        "id": "664f1a2b3c4d5e6f7a8b9c0e",
                        "theme_name": "Light Mode",
                        "theme_image_url": "https://cdn.example.com/themes/light.jpg",
                        "delete": False,
                    }
                ],
                "icons": [],
                "widgets": [],
            }
        }
    )

    wallpaper_id: str = Field(..., description="Wallpaper ka ObjectId — required.")
    category_name: Optional[str] = Field(default=None, max_length=150)
    title: Optional[str] = Field(default=None, max_length=255)
    home_wallpaper_url: Optional[str] = Field(default=None, max_length=1024)
    lock_wallpaper_url: Optional[str] = Field(default=None, max_length=1024)
    themes: Optional[List[ThemeUpdate]] = Field(default=None)
    icons: Optional[List[IconUpdate]] = Field(default=None)
    widgets: Optional[List[WidgetUpdate]] = Field(default=None)

    @field_validator("category_name", "title", "home_wallpaper_url", "lock_wallpaper_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Optional[str]) -> Optional[str]:
        """Empty string bhejo ya null — dono ka matlab 'mat update karo'."""
        if value == "" or value is None:
            return None
        return value

    @field_validator("home_wallpaper_url", "lock_wallpaper_url", mode="after")
    @classmethod
    def validate_url_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_url(value)


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------
class WallpaperResponse(BaseModel):
    id: str
    title: str
    home_wallpaper_url: str
    lock_wallpaper_url: str
    category: CategoryResponse
    themes: List[ThemeResponse] = Field(default_factory=list)
    icons: List[IconResponse] = Field(default_factory=list)
    widgets: List[WidgetResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WallpaperListItemResponse(BaseModel):
    """Lightweight response used in list endpoints (no nested themes/icons/widgets)."""

    id: str
    title: str
    home_wallpaper_url: str
    lock_wallpaper_url: str
    category: CategoryResponse
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    url: str = Field(..., description="The resulting (mock or real) S3 URL")
    filename: str
