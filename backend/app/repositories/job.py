"""Generation job repository."""
from __future__ import annotations

from app.models import GenerationJob
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    model = GenerationJob


job_repository = JobRepository()
