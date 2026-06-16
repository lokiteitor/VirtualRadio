"""Host agent.

Produces the host-driven framing segments of the show: the intro, the per-block
music tee (a single line that hands off to a back-to-back block of songs), the
music segments themselves and the outro. Intro/outro lines are drawn from the
station's ``intro_templates`` / ``outro_templates`` (falling back to generic
Spanish lines if a station has none).

The host hands off to a whole music block ONCE and stays silent until the block
ends; he never mentions the commercials that follow a block.
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


def intro_segment(station) -> dict[str, Any]:
    """Host intro greeting. Uses the station's intro templates.

    Stays a plain greeting: the song that opens the first music block is named
    by :func:`music_tee_segment`, not here, so the intro can be followed by talk
    (news / callers) before any music plays.
    """
    intro_text = _choice(getattr(station, "intro_templates", None) or [], _FALLBACK_INTROS)
    intro_text += " Hoy tenemos un programa cargado de sorpresas. ¡Acomódense!"
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


def music_tee_segment(
    first_track: dict[str, Any] | None, *, opening: bool
) -> dict[str, Any]:
    """Single host line handing off to a back-to-back block of songs.

    Introduces the whole block ONCE (the host stays silent until the block
    ends). Names at most the first song of the block and never mentions the
    commercials that follow it. ``opening`` selects the first-block wording vs.
    the "we're back" wording used for later blocks.
    """
    if first_track:
        lead = f"{first_track['artist']} con '{first_track['title']}'"
    else:
        lead = "buena música"
    if opening:
        text = (
            f"¡Y arrancamos con la música! Para abrir, {lead}. Quédense ahí, que vienen "
            "varios temas seguidos. ¡Suban el volumen!"
        )
    else:
        text = (
            f"De vuelta al aire. Seguimos con más buena música; ahora suena {lead}, y van "
            "varios temas sin parar. ¡No se vayan!"
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
