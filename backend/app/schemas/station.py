"""Station request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.schemas.common import BaseSchema


class StationInputSchema(BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    host_name = fields.Str(allow_none=True, validate=validate.Length(max=120))
    description = fields.Str(allow_none=True)
    personality = fields.Str(allow_none=True)
    frequency = fields.Str(allow_none=True, validate=validate.Length(max=20))
    emoji = fields.Str(allow_none=True, validate=validate.Length(max=16))
    color = fields.Str(allow_none=True, validate=validate.Length(max=9))
    intro_templates = fields.List(fields.Str(), load_default=list)
    outro_templates = fields.List(fields.Str(), load_default=list)


class StationSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    name = fields.Str()
    host_name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    personality = fields.Str(allow_none=True)
    frequency = fields.Str(allow_none=True)
    emoji = fields.Str(allow_none=True)
    color = fields.Str(allow_none=True)
    intro_templates = fields.List(fields.Str())
    outro_templates = fields.List(fields.Str())
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


station_input_schema = StationInputSchema()
station_schema = StationSchema()
stations_schema = StationSchema(many=True)
