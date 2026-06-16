"""Celery task that produces a radio episode from a ``GenerationJob``.

Ports the prototype's ``run_generation_pipeline`` status flow to a persisted,
owner-scoped Celery task. The task runs inside the Flask app context (no request
context) so it never uses ``flask_jwt_extended.current_user`` / ``scoped_query``:
the job carries ``owner_id`` and ``station_id`` and every query is filtered
explicitly on ``owner_id`` against ``db.session``.

Job state (status + progress) is persisted at each step using
``app.models.enums.JobStatus``; on any exception the job is marked ``FAILED``
with the error string and the traceback is logged.
"""
from __future__ import annotations

import logging
import traceback

from celery import shared_task
from sqlalchemy import func

from app.extensions import db
from app.models import (
    Character,
    CharacterMemory,
    Episode,
    GenerationJob,
    MusicTrack,
    Station,
)
from app.models.enums import JobStatus
from app.services.agents import episode_assembly

logger = logging.getLogger(__name__)


def _resolve_tracks(owner_id, track_ids):
    """Return owned ``MusicTrack`` rows for ``track_ids`` preserving their order."""
    if not track_ids:
        return []
    rows = (
        db.session.query(MusicTrack)
        .filter(MusicTrack.owner_id == owner_id)
        .filter(MusicTrack.id.in_(track_ids))
        .all()
    )
    by_id = {row.id: row for row in rows}
    return [by_id[tid] for tid in track_ids if tid in by_id]


@shared_task(name="tasks.generate_episode")
def generate_episode_task(job_id: str):
    """Generate, persist and compile a radio episode for the given job."""
    # Lazy imports for the heavy audio stack keep the module import-safe.
    from app.integrations import audio_engine, tts_client

    job = db.session.get(GenerationJob, job_id)
    if job is None:
        logger.warning("GenerationJob %s not found; nothing to do.", job_id)
        return None

    try:
        # 1. Planning.
        job.status = JobStatus.PLANNING
        job.progress = 10
        db.session.commit()

        # 2. Load the (owner-scoped) station + ensure media assets exist.
        station = (
            db.session.query(Station)
            .filter(Station.id == job.station_id)
            .filter(Station.owner_id == job.owner_id)
            .first()
        )
        if station is None:
            raise ValueError(
                f"Station {job.station_id} not found for owner {job.owner_id}"
            )

        audio_engine.ensure_fx_assets()
        # Generate mock tracks if the user has none AND register them in the DB,
        # so the planner (which queries MusicTrack) finds playable audio.
        from app.services.music_indexer import ensure_owner_music

        ensure_owner_music(job.owner_id)

        # Per-station script settings (created with defaults on first use).
        from app.services.episode_settings import get_or_create_for_station

        settings = get_or_create_for_station(job.owner_id, station.id)

        # 3. Assemble the episode (agents + LLM/procedural script).
        result = episode_assembly.build_episode(job.owner_id, station, settings)

        # 4. Persist the episode with a deterministic per-station number. Lock the
        #    station row so concurrent generations of the SAME station serialize
        #    (other stations stay parallel); the unique constraint is the backstop.
        db.session.query(Station).filter(
            Station.id == station.id, Station.owner_id == job.owner_id
        ).with_for_update().first()
        last_number = (
            db.session.query(func.max(Episode.episode_number))
            .filter(
                Episode.owner_id == job.owner_id,
                Episode.station_id == station.id,
            )
            .scalar()
        )
        episode_number = (last_number or 0) + 1
        episode = Episode(
            owner_id=job.owner_id,
            station_id=station.id,
            episode_number=episode_number,
            title=f"{station.name} - Episodio {episode_number}",
            script_json=result["script_json"],
        )
        db.session.add(episode)
        db.session.commit()
        job.episode_id = episode.id
        db.session.commit()

        # 5. Synthesizing.
        job.status = JobStatus.SYNTHESIZING
        job.progress = 50
        db.session.commit()

        # 6. Mixing: resolve tracks and compile the final MP3.
        job.status = JobStatus.MIXING
        job.progress = 75
        db.session.commit()

        tracks = _resolve_tracks(job.owner_id, result["track_ids"])
        rel_path, duration = audio_engine.compile_episode(
            episode, tracks, tts_client.get_tts_audio
        )
        episode.audio_path = rel_path
        episode.duration = duration
        db.session.commit()

        # 7. Persist caller memory + bump last_appearance for each caller.
        for caller in result["callers"]:
            db.session.add(
                CharacterMemory(
                    owner_id=job.owner_id,
                    character_id=caller["character_id"],
                    episode_id=episode.id,
                    memory=caller["caller_summary"] or "...",
                    importance=5,
                )
            )
            character = (
                db.session.query(Character)
                .filter(Character.id == caller["character_id"])
                .filter(Character.owner_id == job.owner_id)
                .first()
            )
            if character is not None:
                character.last_appearance = func.now()
        if result["callers"]:
            db.session.commit()

        # 8. Completed.
        job.status = JobStatus.COMPLETED
        job.progress = 100
        db.session.commit()
        return str(episode.id)

    except Exception as exc:  # noqa: BLE001 - persist failure state for the API
        db.session.rollback()
        logger.error(
            "Generation job %s failed:\n%s", job_id, traceback.format_exc()
        )
        # Re-load the job in case the session was rolled back / detached.
        job = db.session.get(GenerationJob, job_id)
        if job is not None:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            db.session.commit()
        return None
