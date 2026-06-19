"""Generation job response schemas."""
from __future__ import annotations

from marshmallow import fields

from app.models.enums import JobStatus
from app.schemas.common import BaseSchema


class JobSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    station_id = fields.UUID(dump_only=True)
    episode_id = fields.UUID(dump_only=True, allow_none=True)
    status = fields.Enum(JobStatus, by_value=True)
    progress = fields.Int()
    error = fields.Str(allow_none=True)
    # AI usage aggregates (cost auditing); detail at GET /jobs/{id}/traces.
    llm_calls = fields.Int(dump_only=True)
    llm_tokens_in = fields.Int(dump_only=True)
    llm_tokens_out = fields.Int(dump_only=True)
    tts_calls = fields.Int(dump_only=True)
    tts_cached = fields.Int(dump_only=True)
    tts_tokens = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


job_schema = JobSchema()
jobs_schema = JobSchema(many=True)
