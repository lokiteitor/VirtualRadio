"""Gemini TTS client with filesystem caching and graceful degradation.

Synthesis uses the google-genai SDK (Vertex AI with ADC, or the Developer API
key) → soft synthetic fallback clip. The function never raises: any error
degrades to a quiet placeholder so episode compilation keeps working without any
AI provider configured.

The filesystem cache (``MEDIA_ROOT/vox/vox_<hash>.mp3``) is the source of truth.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from typing import Any

from pydub import AudioSegment
from pydub.generators import Sine

from app.integrations import genai_client
from app.models.enums import GeminiVoice
from app.services import usage_collector

logger = logging.getLogger(__name__)

# Prebuilt Gemini voices mapped per role (defaults when nothing is configured).
ROLE_VOICES: dict[str, str] = {
    "host": "Charon",
    "reporter": "Kore",
    "caller": "Puck",
    "commercial": "Fenrir",
}
_DEFAULT_VOICE = "Charon"

# All valid Gemini voice names; lets ``_resolve_voice`` accept either a role
# alias or an explicit voice name (configured per station/character/commercial).
_VALID_VOICES = frozenset(v.value for v in GeminiVoice)


def _resolve_voice(role_or_voice: str) -> str:
    """Resolve a role alias or an explicit Gemini voice name to a voice name."""
    if role_or_voice in _VALID_VOICES:
        return role_or_voice
    return ROLE_VOICES.get(role_or_voice, _DEFAULT_VOICE)

# Gemini TTS returns signed 16-bit little-endian PCM, mono, at 24 kHz.
_PCM_SAMPLE_WIDTH = 2
_PCM_FRAME_RATE = 24000
_PCM_CHANNELS = 1


def _cfg(key: str, env: str, default: Any = None) -> Any:
    try:
        from flask import current_app

        if current_app:
            return current_app.config.get(key, os.environ.get(env, default))
    except Exception:  # pragma: no cover - outside app context
        pass
    return os.environ.get(env, default)


def _vox_dir() -> str:
    media_root = _cfg("MEDIA_ROOT", "MEDIA_ROOT", "/data/media")
    vox_dir = os.path.join(media_root, "vox")
    os.makedirs(vox_dir, exist_ok=True)
    return vox_dir


def _cache_key(text_clean: str, role: str) -> str:
    return hashlib.md5(f"{text_clean}_{role}".encode("utf-8")).hexdigest()


def _fallback_clip(text_clean: str) -> AudioSegment:
    """Return a soft synthetic clip sized to the text (~3 words/sec, min 500ms)."""
    word_count = len(text_clean.split())
    estimated_duration_ms = max(500, int((word_count / 3.0) * 1000))
    beep = Sine(440).to_audio_segment(duration=100, volume=-30)
    silence = AudioSegment.silent(duration=estimated_duration_ms - 100)
    return beep + silence


def _synthesize_genai(client, text_clean: str, role: str, cached_file: str) -> AudioSegment:
    """Synthesize speech via the google-genai SDK, cache the MP3, return the segment."""
    from google.genai import types

    voice = _resolve_voice(role)
    model = genai_client.tts_model()
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )
    started = time.monotonic()
    resp = client.models.generate_content(
        model=model,
        contents=text_clean,
        config=config,
    )
    usage = getattr(resp, "usage_metadata", None)
    tokens_in = getattr(usage, "prompt_token_count", 0) or 0
    tokens_out = getattr(usage, "candidates_token_count", 0) or 0
    usage_collector.record(
        "tts",
        "gemini",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        total_tokens=getattr(usage, "total_token_count", 0) or (tokens_in + tokens_out),
        latency_ms=int((time.monotonic() - started) * 1000),
    )
    pcm = resp.candidates[0].content.parts[0].inline_data.data
    if isinstance(pcm, str):  # some SDK paths return base64 text
        pcm = base64.b64decode(pcm)

    segment = AudioSegment(
        data=pcm,
        sample_width=_PCM_SAMPLE_WIDTH,
        frame_rate=_PCM_FRAME_RATE,
        channels=_PCM_CHANNELS,
    )
    segment.export(cached_file, format="mp3")
    return segment


def get_tts_audio(text: str, role: str) -> AudioSegment:
    """Synthesize ``text`` for ``role`` (or load from cache). Never raises.

    Blank text yields 500ms of silence. When an AI provider is configured the
    Gemini TTS model is used; on any error (or no provider) a soft synthetic clip
    sized to the text is returned instead.
    """
    text_clean = (text or "").strip()
    if not text_clean:
        return AudioSegment.silent(duration=500)

    file_hash = _cache_key(text_clean, role)
    cached_file = os.path.join(_vox_dir(), f"vox_{file_hash}.mp3")

    # Filesystem cache is the source of truth. A cache hit costs nothing (the clip
    # was synthesized once before), so it's traced as cached=True with no tokens.
    if os.path.exists(cached_file):
        try:
            segment = AudioSegment.from_file(cached_file)
            usage_collector.record("tts", "gemini", model=genai_client.tts_model(), cached=True)
            return segment
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load cached TTS clip %s: %s", cached_file, exc)

    client = genai_client.get_client()
    if client is not None:
        try:
            segment = _synthesize_genai(client, text_clean, role, cached_file)
            return segment
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Gemini TTS synthesis failed for role '%s': %s; using fallback",
                role,
                exc,
            )

    usage_collector.record("tts", "synthetic")
    return _fallback_clip(text_clean)


def apply_telephony_filter(segment: AudioSegment) -> AudioSegment:
    """Apply a 300-3000 Hz bandpass so audio sounds like a phone call."""
    return segment.high_pass_filter(300).low_pass_filter(3000)
