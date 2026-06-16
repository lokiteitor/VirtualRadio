"""Commercial repository."""
from __future__ import annotations

from app.models import Commercial
from app.repositories.base import BaseRepository


class CommercialRepository(BaseRepository):
    model = Commercial


commercial_repository = CommercialRepository()
