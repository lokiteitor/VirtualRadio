"""Story event request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.models.enums import StoryStatus
from app.schemas.common import BaseSchema


class StoryEventInputSchema(BaseSchema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    related_characters = fields.Str(allow_none=True)
    status = fields.Enum(StoryStatus, by_value=True, load_default=StoryStatus.ACTIVE)
    resolved_at = fields.DateTime(allow_none=True)


class StoryEventSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    title = fields.Str()
    description = fields.Str(allow_none=True)
    related_characters = fields.Str(allow_none=True)
    status = fields.Enum(StoryStatus, by_value=True)
    resolved_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


story_event_input_schema = StoryEventInputSchema()
story_event_schema = StoryEventSchema()
story_events_schema = StoryEventSchema(many=True)
