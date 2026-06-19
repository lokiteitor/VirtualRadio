"""Per-call audit trace for AI usage (LLM + TTS) during episode generation.

One row per LLM or TTS call made while generating an episode, so the cost of a
generation can be audited after the fact: provider, model, token counts, whether
a TTS call was served from the on-disk cache (``cached=True`` ⇒ no API cost), and
latency. Written by the Celery worker, so ``owner_id`` is set explicitly from the
job (never from ``current_user``).
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import TRACE_KIND_ENUM_NAME, TraceKind, pg_enum


class GenerationTrace(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "generation_traces"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[TraceKind] = mapped_column(
        pg_enum(TraceKind, TRACE_KIND_ENUM_NAME),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tokens_in: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    tokens_out: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    cached: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, server_default=text("false"), default=False
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
