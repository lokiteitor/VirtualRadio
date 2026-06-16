"""Auth & user schemas."""
from __future__ import annotations

from marshmallow import fields, validate

from app.schemas.common import BaseSchema


class RegisterSchema(BaseSchema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    display_name = fields.Str(allow_none=True, validate=validate.Length(max=120))


class LoginSchema(BaseSchema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class UserSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    email = fields.Email()
    display_name = fields.Str(allow_none=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


register_schema = RegisterSchema()
login_schema = LoginSchema()
user_schema = UserSchema()
