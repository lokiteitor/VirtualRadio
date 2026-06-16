"""News agent.

Turns a planned news item into the spoken segments of a radio newscast: a host
transition into the news, the reporter reading the story, and the host's
station-specific reaction (ported verbatim from the prototype's procedural
script). All text is Spanish and keeps the satirical tone.
"""
from __future__ import annotations

from typing import Any

# Host reactions to the news, keyed by station name (prototype-accurate).
_HOST_REACTIONS: dict[str, str] = {
    "WCTR Sim Edition": (
        "¡Lo sabía! ¡El Cheddar gigante es solo la fase uno del plan espacial "
        "alienígena! No se dejen engañar. Vamos a unos patrocinadores rápidos..."
    ),
    "AgroTalk FM": (
        "Increíble. Cuidado con los neumáticos, amigos. No queremos que terminen "
        "usando queso para labrar el campo. Escuchemos este mensaje comercial..."
    ),
    "Trucker News Radio": (
        "Vaya lío en la carretera. Pink fog y arpas... Suena a que alguien fumó algo "
        "raro en la gasolinera. Ojo al parche, camioneros. Y ahora, publicidad."
    ),
}
_DEFAULT_REACTION = (
    "Un reporte preocupante para nuestra economía agrícola. "
    "Volvemos tras una breve pausa comercial."
)


def transition_segment(host_name: str, prev_artist: str) -> dict[str, Any]:
    """Host segue from the previous song into the news block."""
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


def report_segment(station_name: str, news: dict[str, Any]) -> dict[str, Any]:
    """Reporter reading the news story."""
    full_script = news.get("full_script") or news.get("summary") or news.get("headline", "")
    text = f"Reportando para {station_name}, soy el Corresponsal Virtual. {full_script}"
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
    station_name: str, host_name: str, news: dict[str, Any], prev_artist: str
) -> list[dict[str, Any]]:
    """Full news block: transition + reporter + host reaction."""
    return [
        transition_segment(host_name, prev_artist),
        report_segment(station_name, news),
        reaction_segment(station_name),
    ]
