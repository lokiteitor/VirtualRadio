"""Radio station model."""
from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class Station(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "stations"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_stations_owner_name"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    host_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    intro_templates: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"), default=list
    )
    outro_templates: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"), default=list
    )
