"""Character request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.schemas.common import BaseSchema


class CharacterInputSchema(BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    role = fields.Str(allow_none=True, validate=validate.Length(max=150))
    description = fields.Str(allow_none=True)
    personality = fields.Str(allow_none=True)
    station_affinity = fields.Str(allow_none=True)


class CharacterSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    name = fields.Str()
    role = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    personality = fields.Str(allow_none=True)
    station_affinity = fields.Str(allow_none=True)
    first_appearance = fields.DateTime(dump_only=True)
    last_appearance = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CharacterMemorySchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    character_id = fields.UUID(dump_only=True)
    episode_id = fields.UUID(dump_only=True, allow_none=True)
    memory = fields.Str()
    importance = fields.Int()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


character_input_schema = CharacterInputSchema()
character_schema = CharacterSchema()
characters_schema = CharacterSchema(many=True)
character_memories_schema = CharacterMemorySchema(many=True)
