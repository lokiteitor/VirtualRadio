"""Commercial brand request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.schemas.common import BaseSchema


class BrandInputSchema(BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    description = fields.Str(allow_none=True)
    industry = fields.Str(allow_none=True, validate=validate.Length(max=100))
    slogan = fields.Str(allow_none=True, validate=validate.Length(max=255))
    is_active = fields.Bool(load_default=True)


class BrandSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    name = fields.Str()
    description = fields.Str(allow_none=True)
    industry = fields.Str(allow_none=True)
    slogan = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


brand_input_schema = BrandInputSchema()
brand_schema = BrandSchema()
brands_schema = BrandSchema(many=True)
