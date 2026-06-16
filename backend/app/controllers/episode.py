"""Episode controller: listing, retrieval, deletion, audio and generation.

Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

import logging
import os

from flask import current_app

from app.common.errors import NotFoundError
from app.models import Episode
from app.repositories.episode import episode_repository
from app.repositories.job import job_repository
from app.repositories.station import station_repository
from app.schemas.common import load_or_422
from app.schemas.episode import episode_generate_schema, episode_schema, episodes_schema
from app.schemas.job import job_schema

logger = logging.getLogger(__name__)


def list_episodes(station_id=None) -> list[dict]:
    items = episode_repository.list(
        order_by=Episode.created_at.desc(), station_id=station_id
    )
    return episodes_schema.dump(items)


def get_episode(episode_id) -> dict:
    return episode_schema.dump(episode_repository.get(episode_id))


def _episode_abs_path(episode) -> str | None:
    if not episode.audio_path:
        return None
    media_root = current_app.config["MEDIA_ROOT"]
    return os.path.join(media_root, episode.audio_path)


def delete_episode(episode_id) -> None:
    episode = episode_repository.get(episode_id)  # 404 if missing / not owned
    abs_path = _episode_abs_path(episode)
    episode_repository.delete(episode)
    if abs_path and os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError as exc:  # noqa: BLE001
            logger.warning("Failed to remove episode audio %s: %s", abs_path, exc)


def get_episode_audio_path(episode_id) -> str:
    """Return the absolute MP3 path, raising 404 if missing on disk."""
    episode = episode_repository.get(episode_id)  # 404 if missing / not owned
    abs_path = _episode_abs_path(episode)
    if not abs_path or not os.path.exists(abs_path):
        raise NotFoundError("El audio del episodio no está disponible")
    return abs_path


def generate_episode(payload) -> dict:
    """Validate the station, create a queued job and enqueue the Celery task."""
    data = load_or_422(episode_generate_schema, payload)
    station = station_repository.get_or_none(data["station_id"])
    if station is None:
        raise NotFoundError(
            "La estación indicada no existe o pertenece a otro usuario"
        )

    job = job_repository.create(station_id=station.id)

    try:
        from app.tasks.generation import generate_episode_task

        generate_episode_task.delay(str(job.id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not enqueue generation task for job %s: %s", job.id, exc)

    return job_schema.dump(job)
