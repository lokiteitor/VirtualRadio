"""LLM client with graceful degradation.

Fallback order: Google Gemini (via the google-genai SDK — Vertex AI with ADC or
the Developer API key) → OpenRouter → ``None``. Callers must always handle a
``None`` result and fall back to procedural content, so the system keeps working
without any AI provider configured.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

from app.integrations import genai_client

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _cfg(key: str, env: str, default: Any = None) -> Any:
    try:
        from flask import current_app

        if current_app:
            return current_app.config.get(key, os.environ.get(env, default))
    except Exception:  # pragma: no cover - outside app context
        pass
    return os.environ.get(env, default)


def _complete_gemini(prompt: str, system_instruction: str, json_mode: bool = False) -> str | None:
    client = genai_client.get_client()
    if client is None:
        return None
    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            response_mime_type="application/json" if json_mode else None,
        )
        resp = client.models.generate_content(
            model=genai_client.llm_model(),
            contents=prompt,
            config=config,
        )
        text = getattr(resp, "text", None)
        if text:
            return text
        logger.warning("Gemini returned an empty response; falling back")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini (google-genai) call failed: %s; falling back", exc)
    return None


def _complete_openrouter(prompt: str, system_instruction: str) -> str | None:
    api_key = _cfg("OPENROUTER_API_KEY", "OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    timeout = int(_cfg("LLM_TIMEOUT", "LLM_TIMEOUT", 20) or 20)
    model = _cfg("LLM_MODEL", "LLM_MODEL", "google/gemini-2.5-flash")
    try:
        res = requests.post(
            _OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=timeout,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        logger.warning("OpenRouter returned %s", res.status_code)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenRouter call failed: %s", exc)
    return None


def complete(prompt: str, system_instruction: str = "", json_mode: bool = False) -> str | None:
    """Return raw text from the first available provider, or ``None``."""
    return (
        _complete_gemini(prompt, system_instruction, json_mode)
        or _complete_openrouter(prompt, system_instruction)
    )


def _strip_code_fences(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean[3:]
        if clean[:4].lower() == "json":
            clean = clean[4:]
        if clean.endswith("```"):
            clean = clean[:-3]
    return clean.strip()


def complete_json(prompt: str, system_instruction: str = "") -> Any | None:
    """Return parsed JSON (dict/list) from the LLM, or ``None`` on any failure."""
    text = complete(prompt, system_instruction, json_mode=True)
    if not text:
        return None
    try:
        return json.loads(_strip_code_fences(text))
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse LLM JSON: %s", exc)
        return None
