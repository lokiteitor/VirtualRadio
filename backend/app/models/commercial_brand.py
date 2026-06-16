"""Fictional brand model (shared universe)."""
from __future__ import annotations

from sqlalchemy import Boolean, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class CommercialBrand(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "commercial_brands"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_brands_owner_name"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    slogan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )

    commercials = relationship(
        "Commercial", cascade="all, delete-orphan", passive_deletes=True
    )
