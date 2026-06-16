"""Shared google-genai client factory.

Supports two auth modes, both via the official ``google-genai`` SDK:

* **Vertex AI** (``GEMINI_USE_VERTEX=true``): uses Application Default
  Credentials (ADC) + ``GOOGLE_CLOUD_PROJECT`` + ``GOOGLE_CLOUD_LOCATION``.
* **Gemini Developer API**: uses ``GEMINI_API_KEY``.

Returns ``None`` when neither is configured or the SDK is unavailable, so every
caller degrades gracefully.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _cfg(key: str, env: str, default: Any = None) -> Any:
    try:
        from flask import current_app

        if current_app:
            return current_app.config.get(key, os.environ.get(env, default))
    except Exception:  # pragma: no cover - outside app context
        pass
    return os.environ.get(env, default)


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_client():
    """Return a configured ``google.genai.Client`` (Vertex or Developer API), or None."""
    try:
        from google import genai
    except Exception as exc:  # noqa: BLE001 - SDK not installed
        logger.debug("google-genai not available: %s", exc)
        return None

    if _truthy(_cfg("GEMINI_USE_VERTEX", "GEMINI_USE_VERTEX", "")):
        project = _cfg("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT", "")
        location = _cfg("GOOGLE_CLOUD_LOCATION", "GOOGLE_CLOUD_LOCATION", "global")
        if not project:
            logger.warning("GEMINI_USE_VERTEX set but GOOGLE_CLOUD_PROJECT is empty")
            return None
        try:
            return genai.Client(vertexai=True, project=project, location=location)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vertex genai client init failed: %s", exc)
            return None

    api_key = _cfg("GEMINI_API_KEY", "GEMINI_API_KEY", "")
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("genai client init failed: %s", exc)
            return None

    return None


def llm_model() -> str:
    model = _cfg("LLM_MODEL", "LLM_MODEL", "google/gemini-2.5-flash")
    # The SDK expects a bare model id (strip an optional provider prefix).
    return model.split("/")[-1] if "/" in model else model


def tts_model() -> str:
    return _cfg("GEMINI_TTS_MODEL", "GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
