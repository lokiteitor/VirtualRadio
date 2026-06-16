"""Narrative arc (story event) model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import STORY_STATUS_ENUM_NAME, StoryStatus, pg_enum


class StoryEvent(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "story_events"
    __table_args__ = (Index("ix_events_status", "owner_id", "status"),)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_characters: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StoryStatus] = mapped_column(
        pg_enum(StoryStatus, STORY_STATUS_ENUM_NAME),
        nullable=False,
        server_default=text("'active'"),
        default=StoryStatus.ACTIVE,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
