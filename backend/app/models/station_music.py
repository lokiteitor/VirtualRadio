"""Per-station music selection (whitelist of tracks a station may play).

Records that a music track from the owner's global library is available for a
given station. The episode planner restricts its random pick to these tracks;
when a station has no rows here it falls back to the owner's whole library. The
unique key is the (station, track) pair so the same track can be assigned to
several stations.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin


class StationMusic(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "station_music"
    __table_args__ = (
        UniqueConstraint("station_id", "music_track_id", name="uq_station_music"),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    music_track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("music_tracks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
