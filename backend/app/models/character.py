"""Recurring character model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class Character(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_characters_owner_name"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    station_affinity: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_appearance: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_appearance: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    memories = relationship(
        "CharacterMemory", cascade="all, delete-orphan", passive_deletes=True
    )
