"""
Pydantic schemas — define the shape of API request and response data.

All ids are plain integers (1, 2, 3, ...), matching the database models.
Every entity's Create / Update / Response schemas live together in this
one file so the whole API "shape" is easy to scan in a single place.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_url(value: str) -> str:
    """Shared URL validator: ensures value starts with http:// or https://."""
    if not (value.startswith("http://") or value.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")
    return value


def _validate_url_optional(value: Optional[str]) -> Optional[str]:
    """Same as _validate_url but allows None for optional URL fields."""
    if value is None:
        return value
    return _validate_url(value)


# ----------------------------------------------------------------------
# Category
# ----------------------------------------------------------------------
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------
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
    """Schema for creating a theme nested within wallpaper creation."""
    pass


class ThemeUpdate(BaseModel):
    """Schema for partial updates to an existing theme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "theme_name": "Light Mode",
                "theme_image_url": "https://cdn.example.com/themes/light.jpg",
                "delete": False,
            }
        },
    )

    id: Optional[int] = Field(
        default=None, description="Existing theme id. Omit when adding a new theme."
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
    id: int
    wallpaper_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Icon
# ----------------------------------------------------------------------
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
    """Schema for creating an icon nested within wallpaper creation."""
    pass


class IconUpdate(BaseModel):
    """Schema for partial updates to an existing icon."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "icon_name": "Home",
                "icon_url": "https://cdn.example.com/icons/home.png",
                "delete": False,
            }
        },
    )

    id: Optional[int] = Field(
        default=None, description="Existing icon id. Omit when adding a new icon."
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
    id: int
    wallpaper_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Widget
# ----------------------------------------------------------------------
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
    """Schema for creating a widget nested within wallpaper creation."""
    pass


class WidgetUpdate(BaseModel):
    """Schema for partial updates to an existing widget."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "widget_name": "Weather",
                "widget_url": "https://cdn.example.com/widgets/weather.png",
                "delete": False,
            }
        },
    )

    id: Optional[int] = Field(
        default=None, description="Existing widget id. Omit when adding a new widget."
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
    id: int
    wallpaper_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Wallpaper core fields (used in CREATE)
# ----------------------------------------------------------------------
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


class WallpaperCoreOptional(BaseModel):
    """Used for PATCH-like partial updates of wallpaper core fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Forest Pack",
                "home_wallpaper_url": "https://cdn.example.com/wallpapers/home.jpg",
                "lock_wallpaper_url": "https://cdn.example.com/wallpapers/lock.jpg",
            }
        }
    )

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    home_wallpaper_url: Optional[str] = Field(default=None, max_length=1024)
    lock_wallpaper_url: Optional[str] = Field(default=None, max_length=1024)

    @field_validator("home_wallpaper_url", "lock_wallpaper_url", mode="before")
    @classmethod
    def validate_url_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_url(value)


# ----------------------------------------------------------------------
# Create
# ----------------------------------------------------------------------
class WallpaperCreateRequest(BaseModel):
    """
    Top-level request body for POST /api/v1/wallpapers.

    Category is resolved by name: if it exists it is reused, otherwise
    it is created on the fly.
    """

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


# ----------------------------------------------------------------------
# Update (PATCH-like partial update via PUT)
# ----------------------------------------------------------------------
class WallpaperUpdateRequest(BaseModel):
    """
    Top-level request body for PUT /api/v1/wallpapers/{wallpaper_id}.

    All fields are optional to support partial (PATCH-like) updates.
    Themes/icons/widgets entries:
      - Provide `id` + fields to UPDATE an existing entry.
      - Provide `id` + delete=true to DELETE an existing entry.
      - Omit `id` to ADD a new entry.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_name": "Nature",
                "wallpaper": {
                    "title": "Forest Pack Updated",
                    "home_wallpaper_url": "https://cdn.example.com/wallpapers/home_v2.jpg",
                    "lock_wallpaper_url": "https://cdn.example.com/wallpapers/lock_v2.jpg",
                },
                "themes": [],
                "icons": [],
                "widgets": [],
            }
        }
    )

    category_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    wallpaper: Optional[WallpaperCoreOptional] = Field(default=None)
    themes: Optional[List[ThemeUpdate]] = Field(default=None)
    icons: Optional[List[IconUpdate]] = Field(default=None)
    widgets: Optional[List[WidgetUpdate]] = Field(default=None)


# ----------------------------------------------------------------------
# Response
# ----------------------------------------------------------------------
class WallpaperResponse(BaseModel):
    id: int
    title: str
    home_wallpaper_url: str
    lock_wallpaper_url: str
    category: CategoryResponse
    themes: List[ThemeResponse] = Field(default_factory=list)
    icons: List[IconResponse] = Field(default_factory=list)
    widgets: List[WidgetResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WallpaperListItemResponse(BaseModel):
    """Lightweight response used in list endpoints (no nested themes/icons/widgets)."""

    id: int
    title: str
    home_wallpaper_url: str
    lock_wallpaper_url: str
    category: CategoryResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# Misc
# ----------------------------------------------------------------------
class UploadResponse(BaseModel):
    url: str = Field(..., description="The resulting (mock or real) S3 URL")
    filename: str
