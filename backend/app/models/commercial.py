"""Commercial advertisement model (belongs to a brand)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import GEMINI_VOICE_ENUM_NAME, GeminiVoice, pg_enum


class Commercial(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "commercials"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commercial_brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("30"), default=30.0
    )
    # Configurable read TTS voice (null → "commercial" role default).
    voice: Mapped[GeminiVoice | None] = mapped_column(
        pg_enum(GeminiVoice, GEMINI_VOICE_ENUM_NAME), nullable=True, default=None
    )
    campaign: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
