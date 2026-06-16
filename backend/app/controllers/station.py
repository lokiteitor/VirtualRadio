"""Station controller: orchestrates requests, validation and AI suggestion.

This module is the canonical template for every CRUD-with-suggest resource.
Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

import random

from app.integrations import llm_client
from app.models import Station
from app.repositories.station import station_repository
from app.schemas.common import SuggestRequestSchema, load_or_422
from app.schemas.station import station_input_schema, station_schema, stations_schema

_suggest_schema = SuggestRequestSchema()


def list_stations() -> list[dict]:
    items = station_repository.list(order_by=Station.name.asc())
    return stations_schema.dump(items)


def get_station(station_id) -> dict:
    return station_schema.dump(station_repository.get(station_id))


def _with_default_templates(data: dict) -> dict:
    name = data.get("name", "la emisora")
    host = data.get("host_name") or "tu locutor"
    if not data.get("intro_templates"):
        data["intro_templates"] = [
            f"¡Hola a todos! Bienvenidos a {name} con {host}.",
            f"Estás en sintonía de {name}. Aquí {host} transmitiendo en vivo.",
        ]
    if not data.get("outro_templates"):
        data["outro_templates"] = [
            f"Eso es todo por hoy en {name}. Se despide {host}.",
            f"¡Nos vemos en la próxima transmisión de {name}! Adiós.",
        ]
    return data


def create_station(payload) -> dict:
    data = _with_default_templates(load_or_422(station_input_schema, payload))
    return station_schema.dump(station_repository.create(**data))


def update_station(station_id, payload) -> dict:
    station = station_repository.get(station_id)
    data = load_or_422(station_input_schema, payload)
    return station_schema.dump(station_repository.update(station, **data))


def delete_station(station_id) -> None:
    station = station_repository.get(station_id)  # 404 if missing / not owned
    station_repository.delete(station)


def suggest_station(payload) -> dict:
    """Generate a (non-persisted) station proposal via the LLM with a fallback."""
    hint = load_or_422(_suggest_schema, payload)
    name = (hint.get("context") or {}).get("name")

    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a new fictional radio station. "
        "You must return ONLY a JSON object with the following fields: 'name', "
        "'host_name', 'description', 'personality', 'frequency', 'emoji', 'color', "
        "'intro_templates', and 'outro_templates'. Return pure valid JSON only."
    )
    prompt = "Generate details for a new fictional radio station fitting a simulation setting (rural, farming, truck logistics, or general simulation humor).\n"
    if hint.get("prompt"):
        prompt += f"Extra guidance: {hint['prompt']}\n"
    if name:
        prompt += f"The station name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy, authentic-sounding radio station name.\n"
    prompt += (
        "The 'host_name' should be a single name for the announcer.\n"
        "The 'description' should be a 1-sentence description of the radio station style.\n"
        "The 'personality' should specify the announcer's speech traits or obsession.\n"
        "The 'frequency' should be a random FM frequency (e.g. '102.4 FM').\n"
        "The 'emoji' should be a single matching emoji.\n"
        "The 'color' should be a hex color code (e.g. '#10b981').\n"
        "The 'intro_templates' should be a list of 2 announcer intro lines.\n"
        "The 'outro_templates' should be a list of 2 announcer outro lines."
    )

    suggestion = llm_client.complete_json(prompt, system_instruction)
    if not isinstance(suggestion, dict):
        suggestion = _fallback_station(name)
    elif name:
        suggestion["name"] = name

    # Validate/normalize through the input schema, then shape as output.
    normalized = _with_default_templates(station_input_schema.load(suggestion, partial=True))
    return station_schema.dump(normalized)


def _fallback_station(name: str | None) -> dict:
    fallbacks = [
        {
            "name": name or "Radio Tequila 100",
            "host_name": "Pancho",
            "description": "Estación de música ranchera y debates sobre la fermentación del agave.",
            "personality": "Cheerful, enthusiastic, loves Mexican folk music and spicy food.",
            "frequency": "100.5 FM",
            "emoji": "🌵",
            "color": "#d97706",
            "intro_templates": [
                "¡Ajúa! Bienvenidos a Radio Tequila Cien. Les saluda su compa Pancho. ¡Afínquense que hoy viene música de la buena!",
                "Aquí Pancho reportándose en la cabina de Radio Tequila Cien. Pónganse cómodos y disfruten del mariachi.",
            ],
            "outro_templates": [
                "¡Eso fue todo en Radio Tequila Cien! Pancho les dice adiós. ¡Salud y nos vemos!",
                "Nos vamos, pero volveremos con más picante y música mexicana. Pancho fuera.",
            ],
        },
        {
            "name": name or "Space Rock FM",
            "host_name": "Nova",
            "description": "Estación espacial de rock progresivo y sonidos cósmicos.",
            "personality": "Calm, cosmic traveler, believes the stars vibrate at high rock frequencies.",
            "frequency": "108.0 FM",
            "emoji": "🚀",
            "color": "#8b5cf6",
            "intro_templates": [
                "Transmitiendo desde la órbita baja de la simulación. Les habla Nova para Space Rock FM. Ajusten sus auriculares espaciales.",
                "Bienvenidos a la órbita sónica de Space Rock FM. Nova al micrófono. El viaje comienza ahora.",
            ],
            "outro_templates": [
                "Nova apaga el transmisor cósmico por hoy. Sigan viajando por el espacio profundo de la música.",
                "Esto es todo desde la constelación del rock. Corto y cierro desde Space Rock FM.",
            ],
        },
    ]
    chosen = random.choice(fallbacks)
    if name:
        chosen["name"] = name
    return chosen
