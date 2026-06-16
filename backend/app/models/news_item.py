"""Shared news library model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import (
    NEWS_CATEGORY_ENUM_NAME,
    NEWS_TONE_ENUM_NAME,
    NewsCategory,
    NewsTone,
    pg_enum,
)


class NewsItem(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "news_items"
    __table_args__ = (Index("ix_news_active", "owner_id", "is_active"),)

    headline: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[NewsCategory] = mapped_column(
        pg_enum(NewsCategory, NEWS_CATEGORY_ENUM_NAME), nullable=False
    )
    tone: Mapped[NewsTone] = mapped_column(
        pg_enum(NewsTone, NEWS_TONE_ENUM_NAME), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
