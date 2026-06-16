"""Character controller: CRUD, AI suggestion and narrative memories.

Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

import random

from app.integrations import llm_client
from app.models import Character, CharacterMemory
from app.repositories.base import scoped_query
from app.repositories.character import character_repository
from app.schemas.character import (
    character_input_schema,
    character_memories_schema,
    character_schema,
    characters_schema,
)
from app.schemas.common import SuggestRequestSchema, load_or_422

_suggest_schema = SuggestRequestSchema()


def list_characters() -> list[dict]:
    items = character_repository.list(order_by=Character.name.asc())
    return characters_schema.dump(items)


def get_character(character_id) -> dict:
    return character_schema.dump(character_repository.get(character_id))


def create_character(payload) -> dict:
    data = load_or_422(character_input_schema, payload)
    return character_schema.dump(character_repository.create(**data))


def update_character(character_id, payload) -> dict:
    character = character_repository.get(character_id)
    data = load_or_422(character_input_schema, payload)
    return character_schema.dump(character_repository.update(character, **data))


def delete_character(character_id) -> None:
    character = character_repository.get(character_id)  # 404 if missing / not owned
    character_repository.delete(character)


def list_character_memories(character_id) -> list[dict]:
    character = character_repository.get(character_id)  # 404 if missing / not owned
    memories = (
        scoped_query(CharacterMemory)
        .filter(CharacterMemory.character_id == character.id)
        .order_by(CharacterMemory.created_at.desc())
        .all()
    )
    return character_memories_schema.dump(memories)


def suggest_character(payload) -> dict:
    """Generate a (non-persisted) character proposal via the LLM with a fallback."""
    hint = load_or_422(_suggest_schema, payload)
    name = (hint.get("context") or {}).get("name")

    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a fictional character who could be a caller or regular guest on a simulation radio show. "
        "You must return ONLY a JSON object with the following fields: 'name', 'role', 'description', 'personality', and 'station_affinity'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )

    prompt = (
        "Generate details for a fictional character fitting a simulation radio setting (rural, farming, truck logistics, or general simulation humor).\n"
    )
    if hint.get("prompt"):
        prompt += f"Extra guidance: {hint['prompt']}\n"
    if name:
        prompt += f"The character's name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy, authentic-sounding character name.\n"
    prompt += (
        "The 'role' should be their profession or background (e.g. 'Granjero jubilado', 'Conductora de cisternas', 'Mecánico de tractores').\n"
        "The 'description' should be a 1-2 sentence description of who they are and why they call or listen to the radio.\n"
        "The 'personality' should specify their speech traits or core obsession (e.g. 'Paranoico, habla rápido', 'Tranquilo, pausado, reflexivo').\n"
        "The 'station_affinity' should be a comma-separated list of 1 or 2 stations they listen to. Choose from: ['AgroTalk FM', 'Trucker News Radio', 'SimNation News', 'WCTR Sim Edition']."
    )

    suggestion = llm_client.complete_json(prompt, system_instruction)
    if not isinstance(suggestion, dict):
        suggestion = _fallback_character(name)
    elif name:
        suggestion["name"] = name

    # Validate/normalize through the input schema, then shape as output.
    normalized = character_input_schema.load(suggestion, partial=True)
    return character_schema.dump(normalized)


def _fallback_character(name: str | None) -> dict:
    fallbacks = [
        {
            "name": name or "Gertrudis",
            "role": "Criadora de cabras / Escéptica de la tecnología",
            "description": "Una señora de campo que llama constantemente para culpar a las antenas de 5G por la repentina agresividad de sus cabras de ordeño.",
            "personality": "Obsesiva, testaruda, habla con refranes distorsionados.",
            "station_affinity": "WCTR Sim Edition, AgroTalk FM",
        },
        {
            "name": name or "Rafa 'El Rápido'",
            "role": "Repartidor de paquetería express",
            "description": "Un joven ansioso que conduce una furgoneta de reparto y afirma que la gravedad funciona diferente en los caminos de tierra.",
            "personality": "Hiperactivo, habla extremadamente rápido, paranoico con los límites de velocidad.",
            "station_affinity": "Trucker News Radio",
        },
        {
            "name": name or "Ingeniero Fritz",
            "role": "Especialista en tractores alemanes",
            "description": "Un ingeniero perfeccionista obsesionado con la calibración de válvulas y la eficiencia del motor que llama para corregir los comentarios técnicos del locutor.",
            "personality": "Frío, meticuloso, condescendiente, excesivamente técnico.",
            "station_affinity": "SimNation News, AgroTalk FM",
        },
        {
            "name": name or "Clara 'La Sonámbula'",
            "role": "Conductora nocturna de cisternas",
            "description": "Una conductora de larga distancia que asegura ver castillos medievales flotando sobre la carretera a partir de las 3 AM.",
            "personality": "Soñadora, mística, habla en susurros cansados.",
            "station_affinity": "Trucker News Radio, WCTR Sim Edition",
        },
    ]
    chosen = random.choice(fallbacks)
    if name:
        chosen["name"] = name
    return chosen
