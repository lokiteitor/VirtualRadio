"""Story event controller: orchestrates requests and validation.

Controllers return plain serializable data; routes wrap it in the envelope.
Story events have no /suggest endpoint.
"""
from __future__ import annotations

from app.models import StoryEvent
from app.models.enums import StoryStatus
from app.repositories.story_event import story_event_repository
from app.schemas.common import load_or_422
from app.schemas.story_event import (
    story_event_input_schema,
    story_event_schema,
    story_events_schema,
)


def list_story_events(status: StoryStatus | None = None) -> list[dict]:
    items = story_event_repository.list(
        order_by=StoryEvent.created_at.desc(), status=status
    )
    return story_events_schema.dump(items)


def get_story_event(event_id) -> dict:
    return story_event_schema.dump(story_event_repository.get(event_id))


def create_story_event(payload) -> dict:
    data = load_or_422(story_event_input_schema, payload)
    return story_event_schema.dump(story_event_repository.create(**data))


def update_story_event(event_id, payload) -> dict:
    event = story_event_repository.get(event_id)
    data = load_or_422(story_event_input_schema, payload)
    return story_event_schema.dump(story_event_repository.update(event, **data))


def delete_story_event(event_id) -> None:
    event = story_event_repository.get(event_id)  # 404 if missing / not owned
    story_event_repository.delete(event)
