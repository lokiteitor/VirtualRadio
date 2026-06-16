"""Station repository."""
from __future__ import annotations

from app.models import Station
from app.repositories.base import BaseRepository


class StationRepository(BaseRepository):
    model = Station


station_repository = StationRepository()
