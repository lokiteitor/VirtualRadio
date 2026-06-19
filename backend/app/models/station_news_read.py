"""Per-station news-read ledger.

Records that a news item has already been read on a given station so the episode
planner never picks it again for that station ("read once per station"). The same
news item can still be read on other stations: the unique key is the
(station, news_item) pair, not the news item alone.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class StationNewsRead(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "station_news_reads"
    __table_args__ = (
        UniqueConstraint("station_id", "news_item_id", name="uq_station_news_read"),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("news_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="SET NULL"),
        nullable=True,
    )
