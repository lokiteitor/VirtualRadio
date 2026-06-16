"""Character (caller) agent.

Turns a planned character into the call-in segment of the show: a host intro
opening the phone lines, the caller's line (telephony effect) and the host's
reply. The per-character dialogue is ported from the prototype's
``procedural_script`` and matched by name substring so it works for both the
prototype names and the seeded universe names (e.g. "Silas el Viejo",
"Bob el Camionero"). Spanish, satirical tone preserved.

Also derives a one-line ``caller_summary`` used as a ``CharacterMemory`` after
the episode is produced.
"""
from __future__ import annotations

from typing import Any

# Canned dialogues keyed by a lowercase name substring -> (caller_line, host_reply).
_DIALOGUES: list[tuple[str, str, str]] = [
    (
        "juan",
        "¡Clem! ¡Soy Juan! Te llamo desde la cabina del tractor. ¡Están volando "
        "helicópteros negros sobre mi plantación de remolachas! ¡Y el tractor me está "
        "dando descargas eléctricas cada vez que sintonizo tu programa! ¡Hay un complot "
        "en las ondas!",
        "Tranquilo, Juan. Asegúrate de envolver el radiador en papel de aluminio, eso "
        "debería cortar la señal espía. ¡Gracias por llamar!",
    ),
    (
        "silas",
        "¡Hola! ¿Es aquí donde uno se queja del ruido de los camiones? Ese tarado de Juan "
        "pasó con su tractor haciendo un ruido infernal a las cuatro de la mañana. ¡Y me "
        "debe dos cajas de sidra! ¡Díselo por la radio, Clem!",
        "Mensaje recibido, Silas. Juan, si estás escuchando, págale la sidra al viejo "
        "Silas. Vamos a evitar guerras vecinales.",
    ),
    (
        "bob",
        "Buenas noches, emisora. Habla Big Rig Bob. Estoy cruzando el desfiladero y la "
        "noche está muy despejada. Solo quería mandar un saludo a los muchachos de la "
        "ruta. Y ojo con la niebla rosa de la autopista 9, ¡parece que se mueve sola!",
        "Gracias, Bob. Conduce con cuidado y mantén ese camión estable. Un saludo de "
        "vuelta para ti.",
    ),
    (
        "cynthia",
        "¡Hola! Llamo porque el gallo mecánico del vecino no para de sonar y mi lavanda "
        "orgánica está estresada. ¡El estrés de las plantas reduce su aroma un quince por "
        "ciento! Alguien tiene que intervenir.",
        "Entendido, Cynthia. Haremos un llamado a los dueños de aves mecánicas para que "
        "calmen sus sensores. Gracias por tu reporte.",
    ),
]

_DEFAULT_CALLER_LINE = (
    "Hola, hola. Solo llamaba para reportar que mi tractor va perfecto gracias a "
    "AgroFuel. Saludos a toda la audiencia."
)
_DEFAULT_HOST_REPLY = "¡Eso es lo que nos gusta escuchar! Gracias por llamar, amigo."


def _dialogue_for(name: str) -> tuple[str, str]:
    """Return ``(caller_line, host_reply)`` for *name*, matched by substring."""
    lowered = (name or "").lower()
    for key, caller_line, host_reply in _DIALOGUES:
        if key in lowered:
            return caller_line, host_reply
    return _DEFAULT_CALLER_LINE, _DEFAULT_HOST_REPLY


def intro_segment(host_name: str) -> dict[str, Any]:
    """Host opens the phone lines."""
    text = (
        f"¡Qué buen ritmo! Soy {host_name} y abrimos las líneas telefónicas. "
        "Tenemos una llamada al aire. Hola, ¿quién habla?"
    )
    return {
        "type": "speech",
        "speaker": "Host",
        "text": text,
        "voice_id": "host",
        "effect": None,
        "track_id": None,
        "duration_seconds": 8,
    }


def build_segments(
    host_name: str, character: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Full caller block: host intro + caller line (telephony) + host reply."""
    name = character.get("name") if character else "Silas"
    caller_line, host_reply = _dialogue_for(name)

    return [
        intro_segment(host_name),
        {
            "type": "speech",
            "speaker": "Caller",
            "text": caller_line,
            "voice_id": "caller",
            "effect": "telephony",
            "track_id": None,
            "duration_seconds": 20,
        },
        {
            "type": "speech",
            "speaker": "Host",
            "text": host_reply,
            "voice_id": "host",
            "effect": None,
            "track_id": None,
            "duration_seconds": 12,
        },
    ]


def summarize_caller(
    station_name: str, script_json: list[dict[str, Any]], index: int = 0
) -> str | None:
    """Derive a one-line memory from the ``index``-th caller line in the script.

    Mirrors the prototype: ``Llamó a <station> para hablar sobre: <line>...``.
    With multiple callers, caller lines appear in caller order, so ``index``
    selects the matching caller (falling back to the first). Returns ``None``
    when the script has no caller lines.
    """
    caller_lines = [
        seg.get("text", "")
        for seg in script_json
        if seg.get("speaker") == "Caller" and seg.get("text")
    ]
    if not caller_lines:
        return None
    line = caller_lines[index] if 0 <= index < len(caller_lines) else caller_lines[0]
    return f"Llamó a {station_name} para hablar sobre: {line[:100]}..."
