"""Per-station episode settings controller.

Settings are a 1:1 sub-resource of a station: ownership of the station is
enforced (404 if missing/not owned) and the settings row is created lazily with
defaults on first read. Controllers return plain data; routes wrap the envelope.
"""
from __future__ import annotations

from app.repositories.station import station_repository
from app.repositories.station_episode_settings import (
    station_episode_settings_repository,
)
from app.schemas.common import load_or_422
from app.schemas.station_episode_settings import (
    episode_settings_input_schema,
    episode_settings_schema,
)
from app.services import episode_settings as settings_service


def get_settings(station_id) -> dict:
    station = station_repository.get(station_id)  # 404 if missing / not owned
    row = settings_service.get_or_create_for_current_user(station.id)
    return episode_settings_schema.dump(row)


def update_settings(station_id, payload) -> dict:
    station = station_repository.get(station_id)  # 404 if missing / not owned
    data = load_or_422(episode_settings_input_schema, payload)
    row = settings_service.get_or_create_for_current_user(station.id)
    return episode_settings_schema.dump(
        station_episode_settings_repository.update(row, **data)
    )
