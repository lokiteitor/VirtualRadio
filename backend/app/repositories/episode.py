"""Episode repository."""
from __future__ import annotations

from app.models import Episode
from app.repositories.base import BaseRepository


class EpisodeRepository(BaseRepository):
    model = Episode


episode_repository = EpisodeRepository()
