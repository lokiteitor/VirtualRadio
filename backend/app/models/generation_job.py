"""Async generation job state model (persisted Celery job)."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import OwnerMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import JOB_STATUS_ENUM_NAME, JobStatus, pg_enum


class GenerationJob(UUIDPkMixin, OwnerMixin, TimestampMixin, db.Model):
    __tablename__ = "generation_jobs"
    __table_args__ = (Index("ix_jobs_status", "owner_id", "status"),)

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        pg_enum(JobStatus, JOB_STATUS_ENUM_NAME),
        nullable=False,
        server_default=text("'queued'"),
        default=JobStatus.QUEUED,
    )
    progress: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0"), default=0
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
