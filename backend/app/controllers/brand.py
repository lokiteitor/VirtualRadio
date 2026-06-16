"""Commercial brand controller: orchestrates requests, validation and AI suggestion.

Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

import random

from app.integrations import llm_client
from app.models import CommercialBrand
from app.repositories.brand import brand_repository
from app.schemas.brand import brand_input_schema, brand_schema, brands_schema
from app.schemas.common import SuggestRequestSchema, load_or_422

_suggest_schema = SuggestRequestSchema()


def list_brands() -> list[dict]:
    items = brand_repository.list(order_by=CommercialBrand.name.asc())
    return brands_schema.dump(items)


def get_brand(brand_id) -> dict:
    return brand_schema.dump(brand_repository.get(brand_id))


def create_brand(payload) -> dict:
    data = load_or_422(brand_input_schema, payload)
    return brand_schema.dump(brand_repository.create(**data))


def update_brand(brand_id, payload) -> dict:
    brand = brand_repository.get(brand_id)
    data = load_or_422(brand_input_schema, payload)
    return brand_schema.dump(brand_repository.update(brand, **data))


def delete_brand(brand_id) -> None:
    brand = brand_repository.get(brand_id)  # 404 if missing / not owned
    brand_repository.delete(brand)


def suggest_brand(payload) -> dict:
    """Generate a (non-persisted) brand proposal via the LLM with a fallback."""
    hint = load_or_422(_suggest_schema, payload)
    name = (hint.get("context") or {}).get("name")

    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a fictional company/brand. "
        "You must return ONLY a JSON object with the following fields: 'name', "
        "'slogan', 'industry', and 'description'. "
        "Do not include markdown formatting or block quotes in the outer response. "
        "Return pure valid JSON only."
    )
    prompt = "Generate details for a fictional company/brand fitting a simulation setting (rural, farming, truck logistics, or general simulation humor).\n"
    if hint.get("prompt"):
        prompt += f"Extra guidance: {hint['prompt']}\n"
    if name:
        prompt += f"The company name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy company name.\n"
    prompt += (
        "The 'slogan' should be a funny corporate slogan.\n"
        "The 'industry' should be a single word or short phrase (e.g. 'Agricultura', 'Transporte', 'Tecnología', 'Alimentos', 'Cosméticos').\n"
        "The 'description' should be a 1-2 sentence description of what the company does, matching the absurd humor of the game universe."
    )

    suggestion = llm_client.complete_json(prompt, system_instruction)
    if not isinstance(suggestion, dict):
        suggestion = _fallback_brand(name)
    elif name:
        suggestion["name"] = name

    # Validate/normalize through the input schema, then shape as output.
    normalized = brand_input_schema.load(suggestion, partial=True)
    return brand_schema.dump(normalized)


def _fallback_brand(name: str | None) -> dict:
    fallbacks = [
        {
            "name": name or "GigaFertilizer",
            "slogan": "Si no brilla en la oscuridad, no es nuestro fertilizante.",
            "industry": "Agricultura",
            "description": "Fabricantes del fertilizante número uno enriquecido con uranio de baja intensidad para acelerar la madurez de los tomates.",
        },
        {
            "name": name or "Sleepless Logistics",
            "slogan": "Dormir es para aficionados, entregar es nuestro destino.",
            "industry": "Transporte",
            "description": "Una empresa de mensajería urgente que obliga a sus conductores a beber cinco litros de café por turno para garantizar entregas en tiempo récord.",
        },
        {
            "name": name or "Cabras.Net",
            "slogan": "La red de fibra óptica impulsada por ganado caprino.",
            "industry": "Tecnología",
            "description": "Ofrecemos internet de banda ancha rural conectando rúters directamente a los cuernos de cabras montesas en puntos de alta elevación.",
        },
        {
            "name": name or "Sodapop Sim",
            "slogan": "El refresco con sabor a combustible sintético.",
            "industry": "Bebidas",
            "description": "Una bebida gaseosa sumamente energizante que sabe sospechosamente a diésel pero que mantiene a los camioneros despiertos.",
        },
    ]
    chosen = random.choice(fallbacks)
    if name:
        chosen["name"] = name
    return chosen
