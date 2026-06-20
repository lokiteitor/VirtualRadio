"""Per-station music selection repository (owner-scoped).

The whitelist of tracks a station may play. ``set_tracks`` replaces the whole
selection for a station and validates that every requested track belongs to the
current user (a foreign track raises 404, hiding its existence).
"""
from __future__ import annotations

import uuid

from app.common.errors import NotFoundError
from app.extensions import db
from app.models import MusicTrack, StationMusic
from app.repositories.base import BaseRepository, coerce_uuid, current_owner_id


class StationMusicRepository(BaseRepository):
    model = StationMusic

    def list_track_ids(self, station_id: uuid.UUID) -> list[uuid.UUID]:
        """Return the music track ids assigned to ``station_id``."""
        rows = (
            self.query()
            .filter(StationMusic.station_id == station_id)
            .with_entities(StationMusic.music_track_id)
            .all()
        )
        return [r[0] for r in rows]

    def set_tracks(
        self, station_id: uuid.UUID, track_ids: list[uuid.UUID]
    ) -> list[uuid.UUID]:
        """Replace the station's selection with ``track_ids`` (deduped, validated).

        Every id must belong to the current user; an unknown/foreign id raises
        ``NotFoundError``. Returns the persisted track ids.
        """
        wanted: list[uuid.UUID] = []
        seen: set[uuid.UUID] = set()
        for raw in track_ids:
            uid = coerce_uuid(raw)
            if uid is None:
                raise NotFoundError()
            if uid not in seen:
                seen.add(uid)
                wanted.append(uid)

        if wanted:
            owned_rows = (
                db.session.query(MusicTrack.id)
                .filter(
                    MusicTrack.owner_id == current_owner_id(),
                    MusicTrack.id.in_(wanted),
                )
                .all()
            )
            owned = {r[0] for r in owned_rows}
            if owned != seen:
                raise NotFoundError()

        self.query().filter(StationMusic.station_id == station_id).delete(
            synchronize_session=False
        )
        for uid in wanted:
            db.session.add(
                StationMusic(
                    owner_id=current_owner_id(),
                    station_id=station_id,
                    music_track_id=uid,
                )
            )
        self._commit()
        return wanted


station_music_repository = StationMusicRepository()
