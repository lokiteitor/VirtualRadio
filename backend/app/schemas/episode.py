"""Episode request/response schemas."""
from __future__ import annotations

from marshmallow import fields

from app.schemas.common import BaseSchema


class EpisodeGenerateSchema(BaseSchema):
    station_id = fields.UUID(required=True)


class EpisodeSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    station_id = fields.UUID(dump_only=True)
    title = fields.Str()
    duration = fields.Float()
    script_json = fields.List(fields.Dict())
    audio_path = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


episode_generate_schema = EpisodeGenerateSchema()
episode_schema = EpisodeSchema()
episodes_schema = EpisodeSchema(many=True)
