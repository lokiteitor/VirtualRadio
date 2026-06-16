"""Commercial controller: orchestrates requests, validation and AI suggestion.

Commercials belong to a brand (``CommercialBrand``). Every write validates that
the referenced brand exists and is owned by the current user; otherwise a 404 is
raised so a brand owned by another user is indistinguishable from a missing one.
"""
from __future__ import annotations

from app.common.errors import NotFoundError
from app.integrations import llm_client
from app.models import Commercial, CommercialBrand
from app.repositories.base import coerce_uuid, scoped_query
from app.repositories.commercial import commercial_repository
from app.schemas.commercial import (
    commercial_input_schema,
    commercial_schema,
    commercials_schema,
)
from app.schemas.common import SuggestRequestSchema, load_or_422

_suggest_schema = SuggestRequestSchema()

_BRAND_NOT_FOUND = "La marca indicada no existe o pertenece a otro usuario"


def _get_owned_brand(brand_id) -> CommercialBrand:
    """Return the brand owned by the current user, or raise 404."""
    uid = coerce_uuid(brand_id)
    brand = None
    if uid is not None:
        brand = scoped_query(CommercialBrand).filter(CommercialBrand.id == uid).first()
    if brand is None:
        raise NotFoundError(_BRAND_NOT_FOUND)
    return brand


def list_commercials(brand_id=None) -> list[dict]:
    filters = {}
    if brand_id is not None:
        filters["brand_id"] = coerce_uuid(brand_id)
    items = commercial_repository.list(order_by=Commercial.created_at.desc(), **filters)
    return commercials_schema.dump(items)


def get_commercial(commercial_id) -> dict:
    return commercial_schema.dump(commercial_repository.get(commercial_id))


def create_commercial(payload) -> dict:
    data = load_or_422(commercial_input_schema, payload)
    _get_owned_brand(data["brand_id"])  # 404 if missing / not owned
    return commercial_schema.dump(commercial_repository.create(**data))


def update_commercial(commercial_id, payload) -> dict:
    commercial = commercial_repository.get(commercial_id)
    data = load_or_422(commercial_input_schema, payload)
    _get_owned_brand(data["brand_id"])  # 404 if missing / not owned
    return commercial_schema.dump(commercial_repository.update(commercial, **data))


def delete_commercial(commercial_id) -> None:
    commercial = commercial_repository.get(commercial_id)  # 404 if missing / not owned
    commercial_repository.delete(commercial)


def suggest_commercial(payload) -> dict:
    """Generate a (non-persisted) commercial proposal via the LLM with a fallback."""
    hint = load_or_422(_suggest_schema, payload)
    context = hint.get("context") or {}
    brand_id = context.get("brand_id") or (payload or {}).get("brand_id")
    brand = _get_owned_brand(brand_id)  # 404 if missing / not owned

    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate a fictional commercial advertisement for a given brand. "
        "You must return ONLY a JSON object with the following fields: 'title', 'campaign', "
        "and 'script'. Do not include markdown formatting or block quotes in the outer "
        "response. Return pure valid JSON only."
    )
    prompt = (
        "Generate a fictional commercial advertisement for the following brand:\n"
        f"Name: {brand.name}\n"
        f"Industry: {brand.industry or 'Other'}\n"
        f"Slogan: {brand.slogan or ''}\n"
        f"Description: {brand.description or ''}\n\n"
        "The 'title' should be a catchy title for the advertisement.\n"
        "The 'campaign' should be a short name for this ad campaign.\n"
        "The 'script' should be a 3-5 sentence radio commercial script ready to be read by "
        "an announcer (via Text-to-Speech), keeping the tone energetic, fitting the brand, "
        "and including the brand slogan."
    )
    if hint.get("prompt"):
        prompt += f"\nExtra guidance: {hint['prompt']}"

    suggestion = llm_client.complete_json(prompt, system_instruction)
    if not isinstance(suggestion, dict):
        suggestion = _fallback_commercial(brand)

    return {
        "title": suggestion.get("title"),
        "campaign": suggestion.get("campaign"),
        "script": suggestion.get("script"),
    }


def _fallback_commercial(brand: CommercialBrand) -> dict:
    """Procedural fallback ported from the prototype (brand-name based)."""
    brand_name = (brand.name or "").lower()
    industry = brand.industry or "el sector"
    description = brand.description or ""
    slogan = brand.slogan or ""

    title = f"Promo Especial {brand.name}"
    campaign = "Campaña General"
    script = (
        f"¿Buscas lo mejor en {industry}? {brand.name} es la respuesta. {description} "
        f"Recuerda nuestro lema: '{slogan}'. ¡No esperes más y visítanos hoy mismo!"
    )

    if "agrofuel" in brand_name:
        title = "AgroFuel Máxima Potencia"
        campaign = "Lanzamiento"
        script = (
            "¿Cansado de que tu tractor eche humo negro al subir una colina de dos grados? "
            "Cámbiate a AgroFuel Max. Formulado con residuos de patata orgánica para darte "
            "pura potencia. AgroFuel: porque tus cultivos no se van a cosechar solos, y tu "
            "motor tampoco debería quejarse. Recuerda: ¡Mantén tu tractor rugiendo como un "
            "tigre cafeinado!"
        )
    elif "megahaul" in brand_name:
        title = "Conductores MegaHaul al Volante"
        campaign = "Reclutamiento 2026"
        script = (
            "¿Te gusta el café? ¿Te gusta mirar el asfalto durante setenta y dos horas "
            "seguidas? MegaHaul Logistics está contratando. Ofrecemos sueldo competitivo y "
            "un termo de café gratis. MegaHaul: si cabe, lo llevamos; si no cabe, lo "
            "arrastramos."
        )
    elif "farmnet" in brand_name:
        title = "FarmNet Velocidad Rural Extrema"
        campaign = "Promo de Verano"
        script = (
            "¿Se avecina tormenta? Despídete de tu internet. Pero en los días soleados, "
            "experimenta la velocidad de FarmNet. Conectándote al mundo, eventualmente. Es "
            "mejor que hablar con tus vacas."
        )
    elif "tractorcoin" in brand_name:
        title = "El Hype de TractorCoin"
        campaign = "Revolución Cripto"
        script = (
            "¿Por qué invertir en oro cuando puedes invertir en TractorCoin? La única "
            "criptomoneda minada al operar tu cosechadora a las tres de la mañana. "
            "TractorCoin: ara tus ahorros y siémbralos en suelo digital."
        )

    return {"title": title, "campaign": campaign, "script": script}
