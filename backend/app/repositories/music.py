"""Music track repository."""
from __future__ import annotations

from app.models import MusicTrack
from app.repositories.base import BaseRepository


class MusicRepository(BaseRepository):
    model = MusicTrack

    def get_by_hash(self, file_hash: str) -> MusicTrack | None:
        return self.query().filter(self.model.file_hash == file_hash).first()


music_repository = MusicRepository()
