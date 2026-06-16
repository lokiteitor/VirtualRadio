"""Story event repository."""
from __future__ import annotations

from app.models import StoryEvent
from app.repositories.base import BaseRepository


class StoryEventRepository(BaseRepository):
    model = StoryEvent


story_event_repository = StoryEventRepository()
