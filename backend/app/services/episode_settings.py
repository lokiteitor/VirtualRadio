"""Per-station episode settings access (request- and worker-safe).

Mirrors the :mod:`app.services.music_indexer` pattern: a worker-safe core keyed
by an explicit ``owner_id`` (never ``current_user``, so it is usable from the
Celery generation task), plus a thin request-scoped wrapper that derives the
owner from the JWT. Settings rows are created lazily with defaults, which also
provides backward-compatibility for stations created before the table existed.
"""
from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import StationEpisodeSettings


def _find(owner_id: uuid.UUID, station_id: uuid.UUID) -> StationEpisodeSettings | None:
    return (
        db.session.query(StationEpisodeSettings)
        .filter(StationEpisodeSettings.owner_id == owner_id)
        .filter(StationEpisodeSettings.station_id == station_id)
        .first()
    )


def get_or_create_for_station(
    owner_id: uuid.UUID, station_id: uuid.UUID
) -> StationEpisodeSettings:
    """Return the station's episode settings, creating defaults if absent.

    Worker-safe: filters by explicit ``owner_id`` and never uses ``current_user``.
    """
    row = _find(owner_id, station_id)
    if row is not None:
        return row

    row = StationEpisodeSettings(owner_id=owner_id, station_id=station_id)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        # A concurrent generation created it first (uq_episode_settings_station).
        db.session.rollback()
        row = _find(owner_id, station_id)
    return row


def get_or_create_for_current_user(station_id: uuid.UUID) -> StationEpisodeSettings:
    """Request-scoped convenience: owner is taken from the JWT identity."""
    from app.repositories.base import current_owner_id

    return get_or_create_for_station(current_owner_id(), station_id)
