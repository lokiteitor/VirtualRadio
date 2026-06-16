"""Per-station episode script settings model (1:1 with a station).

Holds the configurable script-structure parameters used by the generation
pipeline (how many songs / news / commercials / callers an episode includes,
and how many recent memories to inject per caller). Defaults are tuned for a
radio-like rhythm: 9 songs (3 back-to-back blocks of 3), 1 news, 2 commercials
(recycled into each block's ad break) and 3 callers (one per block return, so
calls are spread across the show). See ``services/agents/episode_assembly``.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import LANGUAGE_ENUM_NAME, Language, pg_enum


class StationEpisodeSettings(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "station_episode_settings"
    __table_args__ = (
        UniqueConstraint("station_id", name="uq_episode_settings_station"),
        CheckConstraint("song_count BETWEEN 0 AND 10", name="ck_episode_settings_song_count"),
        CheckConstraint("news_count BETWEEN 0 AND 5", name="ck_episode_settings_news_count"),
        CheckConstraint("commercial_count BETWEEN 0 AND 5", name="ck_episode_settings_commercial_count"),
        CheckConstraint("caller_count BETWEEN 0 AND 5", name="ck_episode_settings_caller_count"),
        CheckConstraint("memories_per_caller BETWEEN 0 AND 10", name="ck_episode_settings_memories"),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
    )
    song_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("9"), default=9
    )
    news_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("1"), default=1
    )
    commercial_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("2"), default=2
    )
    caller_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3"), default=3
    )
    memories_per_caller: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3"), default=3
    )
    # Script language for generated episodes (defaults to Spanish).
    language: Mapped[Language] = mapped_column(
        pg_enum(Language, LANGUAGE_ENUM_NAME),
        nullable=False,
        server_default=text("'es'"),
        default=Language.SPANISH,
    )
