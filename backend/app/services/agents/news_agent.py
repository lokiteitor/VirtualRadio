"""News agent.

Turns a planned news item into the spoken segments of a radio newscast: a host
transition into the news, the reporter reading the story, and the host's
station-specific reaction. All text is Spanish and keeps the satirical tone.

The host never references the commercials here: the news reaction closes the
story and hands back to the show / music, never to a sponsor or ad break (the
ads run on their own in a dedicated break — see ``episode_assembly``).
"""
from __future__ import annotations

from typing import Any

# Host reactions to the news, keyed by station name. These close the story and
# hand back to the show; they MUST NOT mention sponsors / commercials / ad
# breaks (the host never talks about the commercials).
_HOST_REACTIONS: dict[str, str] = {
    "WCTR Sim Edition": (
        "¡Lo sabía! ¡El Cheddar gigante es solo la fase uno del plan espacial "
        "alienígena! No se dejen engañar, amigos. Seguimos al aire, mantengan la sintonía."
    ),
    "AgroTalk FM": (
        "Increíble. Cuidado con los neumáticos, amigos. No queremos que terminen "
        "usando queso para labrar el campo. Seguimos informando para ustedes."
    ),
    "Trucker News Radio": (
        "Vaya lío en la carretera. Pink fog y arpas... Suena a que alguien fumó algo "
        "raro en la gasolinera. Ojo al parche, camioneros, que seguimos juntos en el aire."
    ),
}
_DEFAULT_REACTION = (
    "Un reporte preocupante para nuestra economía agrícola. "
    "Sigamos atentos a lo que viene en el programa."
)


def transition_segment(host_name: str, prev_artist: str | None) -> dict[str, Any]:
    """Host segue into the news block.

    ``prev_artist`` is the artist of the song that just played; when it is
    ``None`` (the opening of the show, before any music) the segue uses an
    opening variant that does not reference a previous song.
    """
    if prev_artist is None:
        text = (
            f"Arrancamos. Soy {host_name} y abrimos con las noticias de la hora. "
            "Nos reportan lo siguiente..."
        )
    else:
        text = (
            f"Ah, ¡qué gran tema de {prev_artist}! De vuelta al micrófono, soy {host_name}. "
            "Vamos directo con las noticias de la hora. Nos reportan lo siguiente..."
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


def report_segment(news: dict[str, Any]) -> dict[str, Any]:
    """Reporter reading the news story.

    The text deliberately omits the station name so the synthesized audio is
    identical for the same news item across every station, letting the TTS cache
    (keyed on text + role) be reused instead of re-synthesized per station. The
    station identity is carried by the host's transition and reaction segments.
    """
    full_script = news.get("full_script") or news.get("summary") or news.get("headline", "")
    text = f"Les informa el Corresponsal Virtual. {full_script}"
    return {
        "type": "speech",
        "speaker": "Reporter",
        "text": text,
        "voice_id": "reporter",
        "effect": None,
        "track_id": None,
        "duration_seconds": 25,
    }


def reaction_segment(station_name: str) -> dict[str, Any]:
    """Host reaction to the news, leading into the commercial break."""
    text = _HOST_REACTIONS.get(station_name, _DEFAULT_REACTION)
    return {
        "type": "speech",
        "speaker": "Host",
        "text": text,
        "voice_id": "host",
        "effect": None,
        "track_id": None,
        "duration_seconds": 12,
    }


def build_segments(
    station_name: str, host_name: str, news: dict[str, Any], prev_artist: str | None
) -> list[dict[str, Any]]:
    """Full news block: transition + reporter + host reaction."""
    return [
        transition_segment(host_name, prev_artist),
        report_segment(news),
        reaction_segment(station_name),
    ]
