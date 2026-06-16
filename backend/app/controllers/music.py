"""Music library controller: indexing, upload, scan and deletion.

Controllers return plain serializable data; routes wrap it in the envelope.
Music tracks live on disk under ``MEDIA_ROOT/music/<owner_id>/`` and are
deduplicated per owner by their MD5 file hash.
"""
from __future__ import annotations

import hashlib
import os

from flask import current_app
from werkzeug.utils import secure_filename

from app.common.errors import ConflictError, ValidationFailedError
from app.models import MusicTrack
from app.repositories.base import current_owner_id
from app.repositories.music import music_repository
from app.schemas.music import music_track_schema, music_tracks_schema


def _user_music_dir() -> str:
    """Return (and create) the current user's music folder on disk."""
    path = os.path.join(
        current_app.config["MEDIA_ROOT"], "music", str(current_owner_id())
    )
    os.makedirs(path, exist_ok=True)
    return path


def _md5_of_file(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _extract_metadata(file_path: str, filename: str) -> dict:
    """Best-effort MP3 tag/duration extraction with filename fallbacks."""
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
            tag_title = _first_tag(tags, "TIT2")
            tag_artist = _first_tag(tags, "TPE1")
            tag_album = _first_tag(tags, "TALB")
            if tag_title:
                title = tag_title
            if tag_artist:
                artist = tag_artist
            if tag_album:
                album = tag_album
    except Exception:  # noqa: BLE001 - corrupt/missing tags must not break indexing
        pass

    return {"title": title, "artist": artist, "album": album, "duration": duration}


def _first_tag(tags, key: str) -> str | None:
    try:
        value = tags.get(key)
    except Exception:  # noqa: BLE001
        return None
    if value is None:
        return None
    text = getattr(value, "text", None)
    if text:
        candidate = str(text[0]).strip()
        return candidate or None
    candidate = str(value).strip()
    return candidate or None


def list_music() -> list[dict]:
    items = music_repository.list(order_by=MusicTrack.title.asc())
    return music_tracks_schema.dump(items)


def upload_music(file_storage) -> dict:
    """Validate, persist to disk, index and return a new track."""
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise ValidationFailedError(details={"file": ["No se envió ningún archivo"]})

    filename = secure_filename(file_storage.filename)
    if not filename.lower().endswith(".mp3"):
        raise ValidationFailedError(details={"file": ["Solo se permiten archivos .mp3"]})

    music_dir = _user_music_dir()
    dest_path = os.path.join(music_dir, filename)
    file_storage.save(dest_path)

    try:
        file_hash = _md5_of_file(dest_path)
    except OSError as exc:
        _safe_remove(dest_path)
        raise ValidationFailedError(
            details={"file": ["No se pudo leer el archivo subido"]}
        ) from exc

    if music_repository.get_by_hash(file_hash) is not None:
        _safe_remove(dest_path)
        raise ConflictError("Esta pista de música ya existe en tu biblioteca")

    metadata = _extract_metadata(dest_path, filename)
    track = music_repository.create(
        file_path=dest_path, file_hash=file_hash, **metadata
    )
    return music_track_schema.dump(track)


def scan_music() -> dict:
    """Reconcile the DB with the user's music folder on disk."""
    music_dir = _user_music_dir()

    existing = music_repository.list()
    known_hashes = {track.file_hash for track in existing}

    # Remove DB rows whose backing file no longer exists on disk.
    removed = 0
    for track in existing:
        if not os.path.isfile(track.file_path):
            music_repository.delete(track)
            known_hashes.discard(track.file_hash)
            removed += 1

    # Add new .mp3 files found on disk (deduplicated by hash).
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
            music_repository.create(
                file_path=file_path, file_hash=file_hash, **metadata
            )
            known_hashes.add(file_hash)
            added += 1

    total = len(music_repository.list())
    return {"added": added, "removed": removed, "total": total}


def delete_music(music_id) -> None:
    track = music_repository.get(music_id)  # 404 if missing / not owned
    file_path = track.file_path
    music_repository.delete(track)
    _safe_remove(file_path)


def _safe_remove(file_path: str) -> None:
    try:
        os.remove(file_path)
    except OSError:
        pass
