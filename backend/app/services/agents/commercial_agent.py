"""Commercial agent.

Turns a planned commercial into the sponsor read-out segment (ported from the
prototype). Spanish, satirical tone preserved.
"""
from __future__ import annotations

from typing import Any


def build_segment(commercial: dict[str, Any]) -> dict[str, Any]:
    """Sponsor voice reading the commercial script."""
    brand_name = commercial.get("brand_name") or "Patrocinador"
    script = commercial.get("script") or ""
    text = f"Patrocinador de hoy: {brand_name}. {script}".strip()
    return {
        "type": "speech",
        "speaker": "Commercial_Voice",
        "text": text,
        "voice_id": "commercial",
        "effect": None,
        "track_id": None,
        "duration_seconds": 20,
    }


def build_segments(commercial: dict[str, Any]) -> list[dict[str, Any]]:
    """Full commercial block (a single sponsor segment)."""
    return [build_segment(commercial)]
