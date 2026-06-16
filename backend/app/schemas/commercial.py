"""Commercial request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.models.enums import GeminiVoice
from app.schemas.common import BaseSchema


class CommercialInputSchema(BaseSchema):
    brand_id = fields.UUID(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    script = fields.Str(required=True, validate=validate.Length(min=1))
    duration = fields.Float(load_default=30.0)
    voice = fields.Enum(GeminiVoice, by_value=True, allow_none=True, load_default=None)
    campaign = fields.Str(allow_none=True, validate=validate.Length(max=150))
    is_active = fields.Bool(load_default=True)


class CommercialSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    brand_id = fields.UUID()
    title = fields.Str()
    script = fields.Str()
    duration = fields.Float()
    voice = fields.Enum(GeminiVoice, by_value=True, allow_none=True)
    campaign = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


commercial_input_schema = CommercialInputSchema()
commercial_schema = CommercialSchema()
commercials_schema = CommercialSchema(many=True)
