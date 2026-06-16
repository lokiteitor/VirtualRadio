"""User account model."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.permissions import ROLE_PERMISSIONS
from app.extensions import db
from app.models.base import TimestampMixin, UUIDPkMixin

_hasher = PasswordHasher()


class User(UUIDPkMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (Index("uq_users_email", text("lower(email)"), unique=True),)

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )

    # The role is implicit (USER) in v1.0; kept as a column for forward-compat.
    role_code: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'USER'"), default="USER"
    )

    # ORM cascades mirror the DB ON DELETE CASCADE for ergonomic deletes.
    stations = relationship("Station", cascade="all, delete-orphan", passive_deletes=True)
    episodes = relationship("Episode", cascade="all, delete-orphan", passive_deletes=True)
    music_tracks = relationship("MusicTrack", cascade="all, delete-orphan", passive_deletes=True)
    news_items = relationship("NewsItem", cascade="all, delete-orphan", passive_deletes=True)
    brands = relationship("CommercialBrand", cascade="all, delete-orphan", passive_deletes=True)
    commercials = relationship("Commercial", cascade="all, delete-orphan", passive_deletes=True)
    characters = relationship("Character", cascade="all, delete-orphan", passive_deletes=True)
    story_events = relationship("StoryEvent", cascade="all, delete-orphan", passive_deletes=True)

    # --- Password helpers (argon2) ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = _hasher.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        try:
            return _hasher.verify(self.password_hash, raw_password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    @property
    def permissions(self) -> frozenset[str]:
        return ROLE_PERMISSIONS.get(self.role_code, ROLE_PERMISSIONS["USER"])
