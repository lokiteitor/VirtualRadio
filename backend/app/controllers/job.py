"""Generation job controller.

Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

from app.repositories.job import job_repository
from app.repositories.trace import generation_trace_repository
from app.schemas.job import job_schema
from app.schemas.trace import traces_schema


def get_job(job_id) -> dict:
    return job_schema.dump(job_repository.get(job_id))  # 404 if missing / not owned


def get_job_traces(job_id) -> list:
    job = job_repository.get(job_id)  # 404 if missing / not owned
    return traces_schema.dump(generation_trace_repository.list_by_job(job.id))
