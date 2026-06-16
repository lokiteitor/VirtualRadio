"""Periodic maintenance Celery tasks.

The task names match the ``beat_schedule`` configured in
``app.config`` (``tasks.cleanup_old_jobs`` and ``tasks.archive_expired_news``).
Both run inside the Flask app context and query ``db.session`` directly.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from flask import current_app

from app.extensions import db
from app.models import GenerationJob, NewsItem
from app.models.enums import JobStatus

logger = logging.getLogger(__name__)


@shared_task(name="tasks.cleanup_old_jobs")
def cleanup_old_jobs() -> int:
    """Delete terminal (COMPLETED/FAILED) jobs older than the retention window.

    Returns the number of deleted rows.
    """
    retention_days = current_app.config["JOBS_RETENTION_DAYS"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    deleted = (
        db.session.query(GenerationJob)
        .filter(GenerationJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]))
        .filter(GenerationJob.updated_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    logger.info("cleanup_old_jobs: deleted %s job(s) older than %s days", deleted, retention_days)
    return int(deleted or 0)


@shared_task(name="tasks.archive_expired_news")
def archive_expired_news() -> int:
    """Deactivate news items whose ``expires_at`` is in the past.

    Returns the number of archived rows.
    """
    now = datetime.now(timezone.utc)

    archived = (
        db.session.query(NewsItem)
        .filter(NewsItem.expires_at.isnot(None))
        .filter(NewsItem.expires_at < now)
        .filter(NewsItem.is_active.is_(True))
        .update({NewsItem.is_active: False}, synchronize_session=False)
    )
    db.session.commit()
    logger.info("archive_expired_news: archived %s expired news item(s)", archived)
    return int(archived or 0)
