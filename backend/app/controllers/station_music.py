"""Per-station music selection controller.

The station's music whitelist is a sub-resource of a station: ownership of the
station is enforced first (404 if missing/not owned). ``get`` returns the
assigned tracks with full metadata; ``set`` replaces the whole selection.
Controllers return plain data; routes wrap the envelope.
"""
from __future__ import annotations

from app.models import MusicTrack
from app.repositories.base import scoped_query
from app.repositories.station import station_repository
from app.repositories.station_music import station_music_repository
from app.schemas.common import load_or_422
from app.schemas.music import music_tracks_schema
from app.schemas.station_music import station_music_input_schema


def _dump_tracks(track_ids) -> list[dict]:
    """Return the owned tracks for ``track_ids`` (ordered by title)."""
    if not track_ids:
        return []
    rows = (
        scoped_query(MusicTrack)
        .filter(MusicTrack.id.in_(track_ids))
        .order_by(MusicTrack.title)
        .all()
    )
    return music_tracks_schema.dump(rows)


def get_station_music(station_id) -> list[dict]:
    station = station_repository.get(station_id)  # 404 if missing / not owned
    return _dump_tracks(station_music_repository.list_track_ids(station.id))


def set_station_music(station_id, payload) -> list[dict]:
    station = station_repository.get(station_id)  # 404 if missing / not owned
    data = load_or_422(station_music_input_schema, payload)
    saved = station_music_repository.set_tracks(station.id, data["track_ids"])
    return _dump_tracks(saved)
