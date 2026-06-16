"""News request/response schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.models.enums import NewsCategory, NewsTone
from app.schemas.common import BaseSchema


class NewsInputSchema(BaseSchema):
    headline = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    summary = fields.Str(allow_none=True)
    full_script = fields.Str(allow_none=True)
    category = fields.Enum(NewsCategory, by_value=True, required=True)
    tone = fields.Enum(NewsTone, by_value=True, required=True)
    is_active = fields.Bool(load_default=True)
    expires_at = fields.DateTime(allow_none=True)


class NewsSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    headline = fields.Str()
    summary = fields.Str(allow_none=True)
    full_script = fields.Str(allow_none=True)
    category = fields.Enum(NewsCategory, by_value=True)
    tone = fields.Enum(NewsTone, by_value=True)
    is_active = fields.Bool()
    expires_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


news_input_schema = NewsInputSchema()
news_schema = NewsSchema()
news_list_schema = NewsSchema(many=True)
