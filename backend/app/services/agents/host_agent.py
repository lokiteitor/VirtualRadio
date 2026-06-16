"""Host agent.

Produces the host-driven framing segments of the show: the intro, the song
introductions, the music segments themselves and the outro. Intro/outro lines are
drawn from the station's ``intro_templates`` / ``outro_templates`` (falling back
to generic Spanish lines if a station has none). Ported from the prototype's
``procedural_script``.
"""
from __future__ import annotations

from typing import Any

# Generic fallbacks if a station has no intro/outro templates configured.
_FALLBACK_INTROS = [
    "¡Hola a todos! Están sintonizando la mejor radio del dial. ¡Empecemos!",
    "Bienvenidos de nuevo a su emisora favorita. Acomódense que arrancamos.",
]
_FALLBACK_OUTROS = [
    "Eso es todo por hoy. ¡Nos escuchamos en la próxima transmisión!",
    "Se acabó el programa. Cuídense mucho y vuelvan pronto. ¡Adiós!",
]


def _choice(items: list[str], fallback: list[str]) -> str:
    import random

    pool = items if items else fallback
    return random.choice(pool)


def intro_segment(station, first_track: dict[str, Any]) -> dict[str, Any]:
    """Host intro, teasing the first song. Uses the station's intro templates."""
    intro_text = _choice(getattr(station, "intro_templates", None) or [], _FALLBACK_INTROS)
    intro_text += (
        f" Hoy escucharemos buena música, como a {first_track['artist']} con su temazo "
        f"'{first_track['title']}'. Pero primero, ¡vamos a la música!"
    )
    return {
        "type": "speech",
        "speaker": "Host",
        "text": intro_text,
        "voice_id": "host",
        "effect": None,
        "track_id": None,
        "duration_seconds": 15,
    }


def music_segment(track: dict[str, Any], track_index: int) -> dict[str, Any]:
    """A music segment whose ``track_id`` is the index into the ordered track list."""
    return {
        "type": "music",
        "speaker": None,
        "text": f"{track['title']} - {track['artist']}",
        "voice_id": None,
        "effect": None,
        "track_id": track_index,
        "duration_seconds": 45,  # short preview snippet for the prototype
    }


def song_intro_segment(track: dict[str, Any], variant: str = "relax") -> dict[str, Any]:
    """Host introducing the next song (a couple of tone variants)."""
    if variant == "last":
        text = (
            "Interesante llamada. Es hora de la última canción del bloque de hoy. "
            f"Con ustedes, {track['artist']} y '{track['title']}'. Regresamos para la "
            "despedida."
        )
    else:
        text = (
            "De regreso. Y ahora es momento de relajarnos un poco con buena música en el "
            f"dial. Aquí tienen a {track['artist']} interpretando '{track['title']}'. "
            "¡Disfrútenla!"
        )
    return {
        "type": "speech",
        "speaker": "Host",
        "text": text,
        "voice_id": "host",
        "effect": None,
        "track_id": None,
        "duration_seconds": 10,
    }


def outro_segment(station) -> dict[str, Any]:
    """Host outro. Uses the station's outro templates."""
    outro_text = _choice(getattr(station, "outro_templates", None) or [], _FALLBACK_OUTROS)
    return {
        "type": "speech",
        "speaker": "Host",
        "text": outro_text,
        "voice_id": "host",
        "effect": None,
        "track_id": None,
        "duration_seconds": 12,
    }
