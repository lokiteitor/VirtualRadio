"""Station episode settings repository."""
from __future__ import annotations

from app.models import StationEpisodeSettings
from app.repositories.base import BaseRepository


class StationEpisodeSettingsRepository(BaseRepository):
    model = StationEpisodeSettings


station_episode_settings_repository = StationEpisodeSettingsRepository()
