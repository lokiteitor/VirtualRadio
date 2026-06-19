"""AI usage trace response schema (cost auditing)."""
from __future__ import annotations

from marshmallow import fields

from app.models.enums import TraceKind
from app.schemas.common import BaseSchema


class TraceSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    job_id = fields.UUID(dump_only=True)
    episode_id = fields.UUID(dump_only=True, allow_none=True)
    kind = fields.Enum(TraceKind, by_value=True)
    provider = fields.Str(dump_only=True)
    model = fields.Str(dump_only=True, allow_none=True)
    tokens_in = fields.Int(dump_only=True)
    tokens_out = fields.Int(dump_only=True)
    total_tokens = fields.Int(dump_only=True)
    cached = fields.Bool(dump_only=True)
    latency_ms = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


trace_schema = TraceSchema()
traces_schema = TraceSchema(many=True)
