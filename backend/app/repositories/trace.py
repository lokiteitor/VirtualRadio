"""AI usage trace repository (owner-scoped)."""
from __future__ import annotations

from app.models import GenerationTrace
from app.repositories.base import BaseRepository


class GenerationTraceRepository(BaseRepository):
    model = GenerationTrace

    def list_by_job(self, job_id):
        """Return this owner's traces for ``job_id``, oldest first."""
        return (
            self.query()
            .filter(GenerationTrace.job_id == job_id)
            .order_by(GenerationTrace.created_at.asc())
            .all()
        )


generation_trace_repository = GenerationTraceRepository()
