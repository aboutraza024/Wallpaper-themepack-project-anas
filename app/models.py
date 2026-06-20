"""
Database models (tables).

Every table uses a simple auto-incrementing integer id (1, 2, 3, ...)
as its primary key. All five models live in this one file so the whole
data layer is easy to scan in a single place.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Current UTC time as a naive datetime — compatible with MySQL DATETIME."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(Base):
    """A wallpaper category, e.g. Nature, Abstract, Minimal."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    wallpapers: Mapped[List["Wallpaper"]] = relationship(
        "Wallpaper",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


class Wallpaper(Base):
    """A wallpaper pack that belongs to exactly one category."""

    __tablename__ = "wallpapers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    home_wallpaper_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    lock_wallpaper_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    category: Mapped["Category"] = relationship(
        "Category", back_populates="wallpapers", lazy="joined"
    )
    themes: Mapped[List["Theme"]] = relationship(
        "Theme",
        back_populates="wallpaper",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    icons: Mapped[List["Icon"]] = relationship(
        "Icon",
        back_populates="wallpaper",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    widgets: Mapped[List["Widget"]] = relationship(
        "Widget",
        back_populates="wallpaper",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Wallpaper id={self.id} title={self.title!r}>"


class Theme(Base):
    """An optional theme attached to a wallpaper."""

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallpaper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallpapers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    theme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    theme_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    wallpaper: Mapped["Wallpaper"] = relationship("Wallpaper", back_populates="themes")

    def __repr__(self) -> str:
        return f"<Theme id={self.id} theme_name={self.theme_name!r}>"


class Icon(Base):
    """An optional icon attached to a wallpaper."""

    __tablename__ = "icons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallpaper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallpapers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    icon_name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    wallpaper: Mapped["Wallpaper"] = relationship("Wallpaper", back_populates="icons")

    def __repr__(self) -> str:
        return f"<Icon id={self.id} icon_name={self.icon_name!r}>"


class Widget(Base):
    """An optional widget attached to a wallpaper."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallpaper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wallpapers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    widget_name: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    wallpaper: Mapped["Wallpaper"] = relationship("Wallpaper", back_populates="widgets")

    def __repr__(self) -> str:
        return f"<Widget id={self.id} widget_name={self.widget_name!r}>"
