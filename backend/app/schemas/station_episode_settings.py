"""Per-station episode settings request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.models.enums import Language
from app.schemas.common import BaseSchema


class EpisodeSettingsInputSchema(BaseSchema):
    # All optional so a PUT may patch any subset; ranges mirror the DB CheckConstraints.
    song_count = fields.Int(validate=validate.Range(min=0, max=10))
    news_count = fields.Int(validate=validate.Range(min=0, max=5))
    commercial_count = fields.Int(validate=validate.Range(min=0, max=5))
    caller_count = fields.Int(validate=validate.Range(min=0, max=5))
    memories_per_caller = fields.Int(validate=validate.Range(min=0, max=10))
    language = fields.Enum(Language, by_value=True)


class EpisodeSettingsSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    station_id = fields.UUID(dump_only=True)
    song_count = fields.Int()
    news_count = fields.Int()
    commercial_count = fields.Int()
    caller_count = fields.Int()
    memories_per_caller = fields.Int()
    language = fields.Enum(Language, by_value=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


episode_settings_input_schema = EpisodeSettingsInputSchema()
episode_settings_schema = EpisodeSettingsSchema()
