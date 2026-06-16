"""Owner-scoped music indexing usable outside a request context (Celery worker).

The HTTP music controller indexes uploads using the JWT identity. The generation
pipeline needs the same indexing keyed by an explicit ``owner_id`` (no request
context), e.g. to register the synthesized mock tracks so the planner — which
queries ``MusicTrack`` — actually finds playable audio.
"""
from __future__ import annotations

import hashlib
import os
import uuid

from flask import current_app

from app.extensions import db
from app.integrations import audio_engine
from app.models import MusicTrack


def _owner_music_dir(owner_id: uuid.UUID) -> str:
    path = os.path.join(current_app.config["MEDIA_ROOT"], "music", str(owner_id))
    os.makedirs(path, exist_ok=True)
    return path


def _md5_of_file(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _extract_metadata(file_path: str, filename: str) -> dict:
    title = os.path.splitext(filename)[0].replace("_", " ").title()
    artist: str | None = None
    album: str | None = None
    duration: float | None = None
    try:
        from mutagen.mp3 import MP3

        audio = MP3(file_path)
        if audio.info is not None and getattr(audio.info, "length", None):
            duration = float(audio.info.length)
        tags = audio.tags
        if tags is not None:
            def _first(key):
                value = tags.get(key)
                text = getattr(value, "text", None) if value is not None else None
                return str(text[0]).strip() if text else None

            title = _first("TIT2") or title
            artist = _first("TPE1") or artist
            album = _first("TALB") or album
    except Exception:  # noqa: BLE001 - corrupt/missing tags must not break indexing
        pass
    return {"title": title, "artist": artist, "album": album, "duration": duration}


def index_owner_music(owner_id: uuid.UUID) -> int:
    """Index any unindexed .mp3 files in the owner's music folder. Returns count added."""
    music_dir = _owner_music_dir(owner_id)
    known_hashes = {
        row[0]
        for row in db.session.query(MusicTrack.file_hash)
        .filter(MusicTrack.owner_id == owner_id)
        .all()
    }
    added = 0
    for root, _dirs, files in os.walk(music_dir):
        for filename in files:
            if not filename.lower().endswith(".mp3"):
                continue
            file_path = os.path.join(root, filename)
            try:
                file_hash = _md5_of_file(file_path)
            except OSError:
                continue
            if file_hash in known_hashes:
                continue
            metadata = _extract_metadata(file_path, filename)
            db.session.add(
                MusicTrack(
                    owner_id=owner_id,
                    file_path=file_path,
                    file_hash=file_hash,
                    **metadata,
                )
            )
            known_hashes.add(file_hash)
            added += 1
    if added:
        db.session.commit()
    return added


def ensure_owner_music(owner_id: uuid.UUID) -> int:
    """Generate mock tracks if the owner has none, then index the folder.

    Returns the number of tracks newly indexed into the database.
    """
    audio_engine.generate_mock_music(owner_id)
    return index_owner_music(owner_id)
