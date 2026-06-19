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
import time
from typing import Any

import requests

from app.integrations import genai_client
from app.services import usage_collector

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _gemini_tokens(resp: Any) -> tuple[int, int, int]:
    """Return ``(in, out, total)`` token counts from a genai response, or zeros."""
    usage = getattr(resp, "usage_metadata", None)
    if usage is None:
        return 0, 0, 0
    tokens_in = getattr(usage, "prompt_token_count", 0) or 0
    tokens_out = getattr(usage, "candidates_token_count", 0) or 0
    total = getattr(usage, "total_token_count", 0) or (tokens_in + tokens_out)
    return tokens_in, tokens_out, total


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
    model = genai_client.llm_model()
    started = time.monotonic()
    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            response_mime_type="application/json" if json_mode else None,
        )
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        text = getattr(resp, "text", None)
        if text:
            tokens_in, tokens_out, total = _gemini_tokens(resp)
            usage_collector.record(
                "llm",
                "gemini",
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                total_tokens=total,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
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
    started = time.monotonic()
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
            body = res.json()
            usage = body.get("usage") or {}
            usage_collector.record(
                "llm",
                "openrouter",
                model=model,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens"),
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            return body["choices"][0]["message"]["content"]
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
