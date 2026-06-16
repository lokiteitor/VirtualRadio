"""Generated episode model (structured script + exported MP3 path)."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class Episode(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "episodes"
    __table_args__ = (
        # Deterministic per-station sequence (1, 2, 3...): the generation worker
        # assigns the next number under a station-row lock; this is the backstop.
        UniqueConstraint("station_id", "episode_number", name="uq_episodes_station_number"),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Per-station auto-incrementing episode number (assigned in the worker).
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    duration: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0"), default=0.0
    )
    script_json: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"), default=list
    )
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
