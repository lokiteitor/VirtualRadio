"""Character repository."""
from __future__ import annotations

from app.models import Character
from app.repositories.base import BaseRepository


class CharacterRepository(BaseRepository):
    model = Character


character_repository = CharacterRepository()
