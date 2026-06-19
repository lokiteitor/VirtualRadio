"""Episode planner agent.

Selects the owner-scoped content elements that the rest of the agents turn into
a script. The counts are driven by the station's :class:`StationEpisodeSettings`
(songs, news items, commercials, callers and memories-per-caller); each picker
returns a *list* honouring its count, padding with procedural ``DEFAULT_*``
fallbacks so generation degrades gracefully when a user has little/no content.

This module runs inside a Celery worker (no request context), so it never relies
on ``flask_jwt_extended.current_user`` / ``scoped_query``: ``owner_id`` is passed
explicitly and every query is filtered on ``Model.owner_id == owner_id`` against
``db.session`` directly. The module is import-safe (no DB access at import time).
"""
from __future__ import annotations

import random
import uuid
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import (
    Character,
    CharacterMemory,
    Commercial,
    CommercialBrand,
    MusicTrack,
    NewsItem,
    StationNewsRead,
)

# --------------------------------------------------------------------------- #
# Procedural fallbacks (ported from the prototype defaults, Spanish satirical)
# --------------------------------------------------------------------------- #
DEFAULT_TRACKS: list[dict[str, Any]] = [
    {"id": None, "title": "Stardew Valley Country Road", "artist": "The Pixels", "duration": 180.0},
    {"id": None, "title": "Highway to Trucking", "artist": "Overdrive", "duration": 210.0},
    {"id": None, "title": "Combine Harvester Blues", "artist": "The Silos", "duration": 195.0},
]

DEFAULT_COMMERCIAL: dict[str, Any] = {
    "brand_name": "AgroFuel",
    "title": "AgroFuel Max",
    "script": "¡Usa AgroFuel y tu tractor volará!",
    "duration": 30.0,
    "voice": None,
}

# Lists used to pad the plural pickers up to the requested count.
DEFAULT_COMMERCIALS: list[dict[str, Any]] = [DEFAULT_COMMERCIAL]


def _owned(model, owner_id: uuid.UUID):
    """Return a base query for *model* filtered to the given owner."""
    return db.session.query(model).filter(model.owner_id == owner_id)


def _pad(rows: list[dict[str, Any]], defaults: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    """Pad ``rows`` with cycled copies of ``defaults`` up to ``count`` items."""
    out = list(rows)
    i = 0
    while len(out) < count and defaults:
        out.append(dict(defaults[i % len(defaults)]))
        i += 1
    return out[:count]


# --------------------------------------------------------------------------- #
# Mappers (DB row -> plain dict)
# --------------------------------------------------------------------------- #
def _track_to_dict(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title or "Tema sin título",
        "artist": row.artist or "Artista Desconocido",
        "duration": row.duration,
    }


def _news_to_dict(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "headline": row.headline,
        "summary": row.summary or "",
        "full_script": row.full_script or row.summary or row.headline,
        "category": row.category.value if hasattr(row.category, "value") else row.category,
        "tone": row.tone.value if hasattr(row.tone, "value") else row.tone,
    }


def _commercial_to_dict(row) -> dict[str, Any]:
    brand = db.session.get(CommercialBrand, row.brand_id)
    return {
        "id": row.id,
        "brand_name": brand.name if brand else "Patrocinador",
        "brand_slogan": brand.slogan if brand else "",
        "title": row.title,
        "script": row.script,
        "duration": row.duration,
        "voice": row.voice.value if row.voice else None,
    }


def _character_to_dict(row, owner_id: uuid.UUID, memories_per_caller: int) -> dict[str, Any]:
    memories: list[str] = []
    if memories_per_caller > 0:
        memories = [
            m.memory
            for m in (
                _owned(CharacterMemory, owner_id)
                .filter(CharacterMemory.character_id == row.id)
                .order_by(CharacterMemory.created_at.desc())
                .limit(memories_per_caller)
                .all()
            )
        ]
    return {
        "id": row.id,
        "name": row.name,
        "role": row.role or "",
        "description": row.description or "",
        "personality": row.personality or "",
        "station_affinity": row.station_affinity or "",
        "memories": memories,
        "voice": row.voice.value if row.voice else None,
    }


# --------------------------------------------------------------------------- #
# Plural pickers (each returns a list honouring ``count``)
# --------------------------------------------------------------------------- #
def pick_tracks(owner_id: uuid.UUID, count: int) -> list[dict[str, Any]]:
    """Pick ``count`` random owned tracks (padded with procedural defaults)."""
    if count <= 0:
        return []
    rows = _owned(MusicTrack, owner_id).order_by(func.random()).limit(count).all()
    return _pad([_track_to_dict(r) for r in rows], DEFAULT_TRACKS, count)


def pick_news_items(
    owner_id: uuid.UUID, count: int, station_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Pick up to ``count`` random active owned news items for ``station_id``.

    Each news item is read at most once per station: items already recorded in
    ``station_news_reads`` for this station are excluded. There is no procedural
    padding here — when the station has exhausted its fresh news (or the owner has
    none), the episode simply gets fewer (or zero) news blocks.
    """
    if count <= 0:
        return []
    already_read = (
        db.session.query(StationNewsRead.news_item_id)
        .filter(StationNewsRead.station_id == station_id)
        .scalar_subquery()
    )
    rows = (
        _owned(NewsItem, owner_id)
        .filter(NewsItem.is_active.is_(True))
        .filter(NewsItem.id.notin_(already_read))
        .order_by(func.random())
        .limit(count)
        .all()
    )
    return [_news_to_dict(r) for r in rows]


def pick_commercials(owner_id: uuid.UUID, count: int) -> list[dict[str, Any]]:
    """Pick ``count`` random active owned commercials + brands (padded)."""
    if count <= 0:
        return []
    rows = (
        _owned(Commercial, owner_id)
        .join(CommercialBrand, Commercial.brand_id == CommercialBrand.id)
        .filter(Commercial.is_active.is_(True))
        .filter(CommercialBrand.is_active.is_(True))
        .order_by(func.random())
        .limit(count)
        .all()
    )
    return _pad([_commercial_to_dict(r) for r in rows], DEFAULT_COMMERCIALS, count)


def _order_by_affinity(characters: list, station_name: str | None) -> list:
    """Shuffle characters, preferring those whose affinity matches the station."""
    pool = list(characters)
    random.shuffle(pool)
    if not station_name:
        return pool
    matching = [
        c
        for c in pool
        if c.station_affinity
        and (station_name in c.station_affinity or "WCTR" in c.station_affinity)
    ]
    rest = [c for c in pool if c not in matching]
    return matching + rest


def pick_characters(
    owner_id: uuid.UUID,
    count: int,
    memories_per_caller: int,
    station_name: str | None = None,
) -> list[dict[str, Any]]:
    """Pick up to ``count`` distinct owned characters (affinity-first).

    Returns a list of length ``count``: real character dicts first, padded with
    ``None`` slots (rendered as a default caller by the character agent), which
    mirrors the prototype's no-character fallback.
    """
    if count <= 0:
        return []
    characters = _owned(Character, owner_id).all()
    ordered = _order_by_affinity(characters, station_name) if characters else []
    chosen = ordered[:count]
    result: list[dict[str, Any] | None] = [
        _character_to_dict(c, owner_id, memories_per_caller) for c in chosen
    ]
    while len(result) < count:
        result.append(None)  # default caller slot
    return result


def language_code(settings) -> str:
    """Return the configured script language as a plain ``"es"`` / ``"en"`` code.

    Tolerates a ``Language`` enum, a plain string, or a missing attribute
    (defaults to Spanish), so it is safe in both the request and worker paths.
    """
    lang = getattr(settings, "language", None)
    code = lang.value if hasattr(lang, "value") else lang
    return code if code in ("es", "en") else "es"


def plan_episode(owner_id: uuid.UUID, station, settings) -> dict[str, Any]:
    """Gather all content elements for an episode of ``station``.

    ``settings`` is a :class:`StationEpisodeSettings`-like object exposing the
    integer counts. Returns lists for ``tracks``/``news``/``commercials`` and a
    ``characters`` list (length ``caller_count``; may contain ``None`` slots).
    """
    station_name = getattr(station, "name", None)
    return {
        "tracks": pick_tracks(owner_id, settings.song_count),
        "news": pick_news_items(owner_id, settings.news_count, station.id),
        "commercials": pick_commercials(owner_id, settings.commercial_count),
        "characters": pick_characters(
            owner_id, settings.caller_count, settings.memories_per_caller, station_name
        ),
    }
