"""News controller: orchestrates requests, validation and AI suggestion.

Controllers return plain serializable data; routes wrap it in the envelope.
"""
from __future__ import annotations

import random

from app.integrations import llm_client
from app.models import NewsItem
from app.models.enums import NewsCategory, NewsTone
from app.repositories.news import news_repository
from app.schemas.common import SuggestRequestSchema, load_or_422
from app.schemas.news import news_input_schema, news_list_schema, news_schema

_suggest_schema = SuggestRequestSchema()


def list_news(*, is_active=None, category=None) -> list[dict]:
    items = news_repository.list(
        order_by=NewsItem.created_at.desc(),
        is_active=is_active,
        category=category,
    )
    return news_list_schema.dump(items)


def get_news(news_id) -> dict:
    return news_schema.dump(news_repository.get(news_id))


def create_news(payload) -> dict:
    data = load_or_422(news_input_schema, payload)
    return news_schema.dump(news_repository.create(**data))


def update_news(news_id, payload) -> dict:
    item = news_repository.get(news_id)
    data = load_or_422(news_input_schema, payload)
    return news_schema.dump(news_repository.update(item, **data))


def delete_news(news_id) -> None:
    item = news_repository.get(news_id)  # 404 if missing / not owned
    news_repository.delete(item)


def _coerce_category(value, fallback: str | None) -> str:
    """Return a valid NewsCategory *value*, preferring *value* then *fallback*."""
    for candidate in (value, fallback):
        if candidate is None:
            continue
        try:
            return NewsCategory(candidate).value
        except ValueError:
            continue
    return random.choice(list(NewsCategory)).value


def _coerce_tone(value, fallback: str | None) -> str:
    for candidate in (value, fallback):
        if candidate is None:
            continue
        try:
            return NewsTone(candidate).value
        except ValueError:
            continue
    return random.choice(list(NewsTone)).value


def suggest_news(payload) -> dict:
    """Generate a (non-persisted) news proposal via the LLM with a fallback."""
    hint = load_or_422(_suggest_schema, payload)
    context = hint.get("context") or {}
    category_hint = context.get("category")
    tone_hint = context.get("tone")

    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate a fictional news item for the game world "
        "(e.g. Farming Simulator, Euro Truck Simulator, etc.). "
        "You must return ONLY a JSON object with the following fields: 'headline', "
        "'summary', 'category', 'tone', and 'full_script'. "
        "Do not include markdown formatting or block quotes in the outer response. "
        "Return pure valid JSON only."
    )

    prompt = (
        "Generate a fictional news item. "
        "The category should be one of: "
        "['Agricultura', 'Transporte', 'Economía', 'Tecnología', 'Clima', "
        "'Comunidad', 'Política Local', 'Sucesos Extraños']. "
        "The tone should be one of: "
        "['Sensacionalista', 'Misterioso', 'Absurdo', 'Serio']. "
    )
    if hint.get("prompt"):
        prompt += f"Extra guidance: {hint['prompt']} "
    if category_hint:
        prompt += f"Use the category '{category_hint}'. "
    if tone_hint:
        prompt += f"Use the tone '{tone_hint}'. "
    prompt += (
        "The 'headline' should be catchy and fitting the tone. "
        "The 'summary' should be a 1-sentence overview. "
        "The 'full_script' should be a 3-5 sentence complete script for a radio news "
        "reporter, ready to be read aloud (via Text-to-Speech)."
    )

    suggestion = llm_client.complete_json(prompt, system_instruction)
    if not isinstance(suggestion, dict):
        suggestion = _fallback_news(category_hint, tone_hint)

    # Coerce category/tone to valid enum values (honoring hints), else fallback.
    suggestion["category"] = _coerce_category(suggestion.get("category"), category_hint)
    suggestion["tone"] = _coerce_tone(suggestion.get("tone"), tone_hint)

    # Validate/normalize through the input schema, then shape as output.
    normalized = news_input_schema.load(suggestion, partial=True)
    return news_schema.dump(normalized)


def _fallback_news(category: str | None, tone: str | None) -> dict:
    fallbacks = [
        {
            "headline": "¡Vacas locas hackean la central lechera!",
            "summary": "Un grupo de vacas modificadas cibernéticamente ha tomado el control de los dispensadores automatizados.",
            "category": "Sucesos Extraños",
            "tone": "Absurdo",
            "full_script": "Atención residentes de la zona rural. Informamos sobre una situación inusual en la Central Lechera Cooperativa. Varias vacas equipadas con implantes experimentales han hackeado el sistema de ordeño automático y ahora exigen un aumento del diez por ciento en su ración diaria de alfalfa orgánica. La policía local aconseja no acercarse a los establos y evitar el contacto visual con cualquier rumiante que lleve luces LED parpadeantes.",
        },
        {
            "headline": "Embote de proporciones épicas en la Ruta 66",
            "summary": "Un camión cargado de patitos de goma gigantes vuelca bloqueando los tres carriles principales.",
            "category": "Transporte",
            "tone": "Sensacionalista",
            "full_script": "Última hora desde las carreteras. El tráfico está completamente paralizado en la Ruta Sesenta y Seis tras el vuelco de un mega-remolque de la empresa MegaHaul. El vehículo transportaba una carga experimental de patos de goma gigantes para parques acuáticos. Miles de patos amarillos de dos metros de altura bloquean ahora ambos sentidos de circulación. Varios camioneros informan que es imposible avanzar y que algunos están usando los patos como sillones inflables improvisados en mitad del asfalto.",
        },
        {
            "headline": "Las lechugas gigantes amenazan la economía local",
            "summary": "Una supercosecha de lechugas mutantes desploma los precios del mercado regional.",
            "category": "Economía",
            "tone": "Serio",
            "full_script": "Buenos días. Informamos del colapso inminente del mercado agrícola. La introducción de un nuevo fertilizante experimental ha producido una cosecha de lechugas gigantes, cada una del tamaño de una casa pequeña. Aunque los agricultores celebraron el tamaño al principio, el exceso de oferta ha destruido el valor del vegetal. En el mercado local, una lechuga ahora se intercambia por medio centavo de TractorCoin. Se aconseja a los productores compostar el excedente antes de que las lechugas comiencen a rodar cuesta abajo hacia el pueblo.",
        },
        {
            "headline": "Avistamiento de OVNIs sobre los silos de grano",
            "summary": "Misteriosas luces verdes en forma de espiral aparecen sobre los silos del pueblo.",
            "category": "Sucesos Extraños",
            "tone": "Misterioso",
            "full_script": "Misterio en los cielos rurales. Anoche, múltiples residentes reportaron un patrón de luces verdes en espiral flotando sobre los silos principales del pueblo. Según testigos presenciales, las luces permanecieron estáticas durante diez minutos antes de emitir un zumbido agudo y desaparecer instantáneamente hacia el norte. La agencia de seguridad nacional no ha emitido comentarios, pero los ufólogos locales sugieren que los visitantes espaciales podrían estar extremadamente interesados en las reservas de trigo de esta temporada.",
        },
    ]

    options = [
        f for f in fallbacks
        if (not category or f["category"] == category) and (not tone or f["tone"] == tone)
    ]
    if not options:
        options = [f for f in fallbacks if (not category or f["category"] == category)]
    if not options:
        options = [f for f in fallbacks if (not tone or f["tone"] == tone)]
    if not options:
        options = fallbacks

    chosen = dict(random.choice(options))
    if category:
        chosen["category"] = category
    if tone:
        chosen["tone"] = tone
    return chosen
