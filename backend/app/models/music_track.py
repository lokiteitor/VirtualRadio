"""Indexed music track model (metadata + MD5 dedup)."""
from __future__ import annotations

from sqlalchemy import CHAR, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class MusicTrack(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "music_tracks"
    __table_args__ = (
        UniqueConstraint("owner_id", "file_hash", name="uq_music_owner_hash"),
        UniqueConstraint("owner_id", "file_path", name="uq_music_owner_path"),
    )

    file_path: Mapped[str] = mapped_column(String(700), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    album: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_hash: Mapped[str] = mapped_column(CHAR(32), nullable=False)
