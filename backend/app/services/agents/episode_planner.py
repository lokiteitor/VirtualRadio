"""Episode planner agent.

Selects the owner-scoped content elements that the rest of the agents turn into
a script: up to 3 random ``MusicTrack`` rows, one active ``NewsItem``, one active
``Commercial`` (plus its ``CommercialBrand``) and one ``Character`` (plus up to 3
of its most recent ``CharacterMemory`` rows).

This module runs inside a Celery worker (no request context), so it never relies
on ``flask_jwt_extended.current_user`` / ``scoped_query``: ``owner_id`` is passed
explicitly and every query is filtered on ``Model.owner_id == owner_id`` against
``db.session`` directly. The module is import-safe (no DB access at import time).

The procedural defaults mirror the prototype so generation degrades gracefully
when a user has no music / news / commercials / characters.
"""
from __future__ import annotations

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
)

# --------------------------------------------------------------------------- #
# Procedural fallbacks (ported from the prototype defaults, Spanish satirical)
# --------------------------------------------------------------------------- #
DEFAULT_TRACKS: list[dict[str, Any]] = [
    {"id": None, "title": "Stardew Valley Country Road", "artist": "The Pixels", "duration": 180.0},
    {"id": None, "title": "Highway to Trucking", "artist": "Overdrive", "duration": 210.0},
    {"id": None, "title": "Combine Harvester Blues", "artist": "The Silos", "duration": 195.0},
]

DEFAULT_NEWS: dict[str, Any] = {
    "headline": "Clima Extremo Amenaza Cosechas",
    "summary": "Una lluvia de sapos de goma ha ralentizado los tractores en la zona este.",
    "full_script": "Los sapos rebotan en el parabrisas y dificultan la labranza.",
    "category": "Clima",
    "tone": "Absurdo",
}

DEFAULT_COMMERCIAL: dict[str, Any] = {
    "brand_name": "AgroFuel",
    "title": "AgroFuel Max",
    "script": "¡Usa AgroFuel y tu tractor volará!",
    "duration": 30.0,
}


def _owned(model, owner_id: uuid.UUID):
    """Return a base query for *model* filtered to the given owner."""
    return db.session.query(model).filter(model.owner_id == owner_id)


def pick_tracks(owner_id: uuid.UUID, limit: int = 3) -> list[dict[str, Any]]:
    """Pick up to ``limit`` random owned music tracks (procedural fallback if none)."""
    rows = (
        _owned(MusicTrack, owner_id)
        .order_by(func.random())
        .limit(limit)
        .all()
    )
    if not rows:
        return [dict(t) for t in DEFAULT_TRACKS[:limit]]

    tracks = [
        {
            "id": row.id,
            "title": row.title or "Tema sin título",
            "artist": row.artist or "Artista Desconocido",
            "duration": row.duration,
        }
        for row in rows
    ]
    return tracks


def pick_news(owner_id: uuid.UUID) -> dict[str, Any]:
    """Pick one random active owned news item (procedural fallback if none)."""
    row = (
        _owned(NewsItem, owner_id)
        .filter(NewsItem.is_active.is_(True))
        .order_by(func.random())
        .first()
    )
    if row is None:
        return dict(DEFAULT_NEWS)

    return {
        "id": row.id,
        "headline": row.headline,
        "summary": row.summary or "",
        "full_script": row.full_script or row.summary or row.headline,
        "category": row.category.value if hasattr(row.category, "value") else row.category,
        "tone": row.tone.value if hasattr(row.tone, "value") else row.tone,
    }


def pick_commercial(owner_id: uuid.UUID) -> dict[str, Any]:
    """Pick one random active owned commercial + its active brand (fallback if none)."""
    row = (
        _owned(Commercial, owner_id)
        .join(CommercialBrand, Commercial.brand_id == CommercialBrand.id)
        .filter(Commercial.is_active.is_(True))
        .filter(CommercialBrand.is_active.is_(True))
        .order_by(func.random())
        .first()
    )
    if row is None:
        return dict(DEFAULT_COMMERCIAL)

    brand = db.session.get(CommercialBrand, row.brand_id)
    return {
        "id": row.id,
        "brand_name": brand.name if brand else "Patrocinador",
        "brand_slogan": brand.slogan if brand else "",
        "title": row.title,
        "script": row.script,
        "duration": row.duration,
    }


def pick_character(owner_id: uuid.UUID, station_name: str | None = None) -> dict[str, Any] | None:
    """Pick one owned character (preferring station affinity) + up to 3 recent memories.

    Returns ``None`` when the owner has no characters at all, mirroring the
    prototype which then falls back to a default caller in the script.
    """
    characters = _owned(Character, owner_id).all()
    if not characters:
        return None

    # Prefer characters whose affinity mentions this station (or the WCTR wildcard).
    chosen = None
    if station_name:
        matching = [
            c
            for c in characters
            if c.station_affinity
            and (station_name in c.station_affinity or "WCTR" in c.station_affinity)
        ]
        if matching:
            chosen = _random_choice(matching)
    if chosen is None:
        chosen = _random_choice(characters)

    memories = (
        _owned(CharacterMemory, owner_id)
        .filter(CharacterMemory.character_id == chosen.id)
        .order_by(CharacterMemory.created_at.desc())
        .limit(3)
        .all()
    )

    return {
        "id": chosen.id,
        "name": chosen.name,
        "role": chosen.role or "",
        "description": chosen.description or "",
        "personality": chosen.personality or "",
        "station_affinity": chosen.station_affinity or "",
        "memories": [m.memory for m in memories],
    }


def _random_choice(items: list):
    """Deterministic-friendly random choice (uses ``random`` lazily)."""
    import random

    return random.choice(items)


def plan_episode(owner_id: uuid.UUID, station) -> dict[str, Any]:
    """Gather all content elements for an episode of ``station``.

    Returns a dict with keys ``tracks``, ``news``, ``commercial`` and
    ``character`` (the latter may be ``None``).
    """
    station_name = getattr(station, "name", None)
    return {
        "tracks": pick_tracks(owner_id, limit=3),
        "news": pick_news(owner_id),
        "commercial": pick_commercial(owner_id),
        "character": pick_character(owner_id, station_name),
    }
