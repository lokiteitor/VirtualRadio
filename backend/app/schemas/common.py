"""Shared schema utilities."""
from __future__ import annotations

from typing import Any

from marshmallow import EXCLUDE, Schema, fields

from app.common.errors import ValidationFailedError


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class SuggestRequestSchema(BaseSchema):
    """Optional hint/context to steer an LLM suggestion."""

    prompt = fields.Str(load_default=None, allow_none=True)
    context = fields.Dict(load_default=dict)


def load_or_422(schema: Schema, data: Any | None) -> dict:
    """Validate a request body, raising the 422 envelope on failure.

    ``owner_id`` (and any unknown key) is ignored — ownership comes from the JWT.
    """
    from marshmallow import ValidationError

    try:
        return schema.load(data or {})
    except ValidationError as exc:
        raise ValidationFailedError(
            details=exc.messages if isinstance(exc.messages, dict) else {"_": exc.messages}
        ) from exc
