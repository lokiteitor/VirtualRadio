"""Episode assembly orchestrator.

``build_episode`` is the single entry point used by the generation task. It:

1. Asks :mod:`episode_planner` to pick the owner-scoped content elements
   (tracks, news, commercial + brand, character + memories).
2. Tries the LLM (:func:`app.integrations.llm_client.complete_json`) with the
   ported "big prompt" for a full script.
3. On ``None`` / invalid output, builds the script procedurally via the
   news / commercial / character / host agents (port of the prototype's
   ``procedural_script``).

Either way it returns the pinned dict::

    {
        "title": str,
        "script_json": list[segment dict],
        "character_id": UUID | None,
        "caller_summary": str | None,
        "track_ids": list[UUID],   # ordered selected MusicTrack ids
    }

Music segments use ``track_id = index into track_ids``.

The module is import-safe: it performs no network/DB access at import time and
imports the LLM client lazily inside :func:`build_episode`.
"""
from __future__ import annotations

import random
import uuid
from typing import Any

from app.services.agents import (
    character_agent,
    commercial_agent,
    episode_planner,
    host_agent,
    news_agent,
)

# Valid segment shape keys (ensures LLM segments are normalized to the contract).
_SEGMENT_KEYS = ("type", "speaker", "text", "voice_id", "effect", "track_id", "duration_seconds")

_LLM_SYSTEM_INSTRUCTION = (
    "You are a professional script writer for a satirical radio generator. You write "
    "funny, immersive radio scripts and output them strictly in JSON format."
)


# --------------------------------------------------------------------------- #
# LLM prompt (ported from the prototype generator.py)
# --------------------------------------------------------------------------- #
def _build_prompt(
    station_name: str,
    host_name: str,
    personality: str,
    news: dict[str, Any],
    commercial: dict[str, Any],
    character: dict[str, Any] | None,
    tracks: list[dict[str, Any]],
) -> str:
    caller_name = character["name"] if character else "Anon"
    caller_role = character["description"] if character else "A listener"
    caller_personality = character["personality"] if character else "Excited"
    caller_memories = character["memories"] if (character and character.get("memories")) else "None"

    # Songs are introduced by index; pad to 3 so the prompt is always well-formed.
    padded = list(tracks) + episode_planner.DEFAULT_TRACKS
    song0, song1, song2 = padded[0], padded[1], padded[2]

    return f"""
        Generate a complete audio show script for the fictional radio station "{station_name}".
        Host Name: {host_name}
        Host Personality: {personality}

        Content elements to include:
        1. News Item: Headline: "{news.get('headline', '')}". Summary: "{news.get('summary', '')}". The host or a reporter should present this news with the station's characteristic tone.
        2. Commercial: Brand: "{commercial.get('brand_name', '')}". Product script to read: "{commercial.get('script', '')}".
        3. Caller Interaction:
           Caller Name: {caller_name}
           Caller Role/Description: {caller_role}
           Caller Personality: {caller_personality}
           Caller Memories/Context: {caller_memories}
           Create a funny phone dialogue where this caller calls the station. The caller should mention or reference their memories. The host responds.
        4. Play 3 songs (Music segments). Introduce each song.

        Generate the output strictly as a JSON list of segments. Do not include markdown code block formatting like ```json ... ```, just the raw JSON.
        Each segment must have:
        - "type": "speech", "music", or "fx"
        - "speaker": "Host", "Caller", "Reporter", "Commercial_Voice", or null (for music/fx)
        - "text": The spoken text or script, or song title for music
        - "voice_id": "host", "caller", "reporter", "commercial", or null
        - "effect": "telephony" (for callers), "ducking" (for speech during music), or null
        - "track_id": The index of the song (0, 1, or 2) if type is music, otherwise null.
        - "duration_seconds": estimate duration (speech ~ 150 words per minute).

        Songs to include:
        - Song 0: "{song0['title']}" by {song0['artist']}
        - Song 1: "{song1['title']}" by {song1['artist']}
        - Song 2: "{song2['title']}" by {song2['artist']}
        """


# --------------------------------------------------------------------------- #
# Procedural script (port of the prototype's procedural_script)
# --------------------------------------------------------------------------- #
def _procedural_script(
    station,
    host_name: str,
    tracks: list[dict[str, Any]],
    news: dict[str, Any],
    commercial: dict[str, Any],
    character: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build a high-quality satirical script procedurally from the agents."""
    station_name = getattr(station, "name", "WCTR Sim Edition")

    # Guarantee three tracks so song intros / music segments are well-formed.
    padded = list(tracks) + episode_planner.DEFAULT_TRACKS
    t0, t1, t2 = padded[0], padded[1], padded[2]

    segments: list[dict[str, Any]] = []

    # Intro + Song 1
    segments.append(host_agent.intro_segment(station, t0))
    segments.append(host_agent.music_segment(t0, 0))

    # News block (transition + reporter + host reaction)
    segments.extend(news_agent.build_segments(station_name, host_name, news, t0["artist"]))

    # Commercial
    segments.extend(commercial_agent.build_segments(commercial))

    # Song 2 intro + Song 2
    segments.append(host_agent.song_intro_segment(t1, variant="relax"))
    segments.append(host_agent.music_segment(t1, 1))

    # Caller block (host intro + caller + host reply)
    segments.extend(character_agent.build_segments(host_name, character))

    # Song 3 intro + Song 3
    segments.append(host_agent.song_intro_segment(t2, variant="last"))
    segments.append(host_agent.music_segment(t2, 2))

    # Outro
    segments.append(host_agent.outro_segment(station))

    return segments


# --------------------------------------------------------------------------- #
# LLM script normalization
# --------------------------------------------------------------------------- #
def _normalize_llm_script(raw: Any) -> list[dict[str, Any]] | None:
    """Validate and normalize an LLM script into the segment contract.

    Returns ``None`` if the structure is not a non-empty list of segment dicts.
    """
    if not isinstance(raw, list) or not raw:
        return None

    normalized: list[dict[str, Any]] = []
    for item in raw:
        # Be tolerant: skip malformed segments instead of discarding the whole
        # script (the LLM occasionally emits an odd entry).
        if not isinstance(item, dict):
            continue
        seg_type = item.get("type")
        if seg_type not in ("speech", "music", "fx"):
            continue
        segment = {key: item.get(key) for key in _SEGMENT_KEYS}
        # Coerce a numeric-string track_id (e.g. "0") to int.
        track_id = segment.get("track_id")
        if isinstance(track_id, str) and track_id.strip().isdigit():
            segment["track_id"] = int(track_id.strip())
        # Ensure a usable duration is present.
        if not isinstance(segment.get("duration_seconds"), (int, float)):
            segment["duration_seconds"] = 10
        normalized.append(segment)
    return normalized or None


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def build_episode(owner_id: uuid.UUID, station) -> dict[str, Any]:
    """Orchestrate the agents and return the pinned episode-assembly dict."""
    from app.integrations import llm_client

    station_name = getattr(station, "name", "WCTR Sim Edition")
    host_name = getattr(station, "host_name", None) or "el Locutor"
    personality = getattr(station, "personality", None) or ""

    # 1. Plan the content elements (owner-scoped).
    plan = episode_planner.plan_episode(owner_id, station)
    tracks = plan["tracks"]
    news = plan["news"]
    commercial = plan["commercial"]
    character = plan["character"]

    # Ordered selected MusicTrack ids (only real DB rows; fallback tracks have id=None).
    track_ids: list[uuid.UUID] = [t["id"] for t in tracks if t.get("id") is not None]

    title = f"{station_name} - Episodio {random.randint(100, 999)}"

    # 2. Try the LLM first.
    script_json: list[dict[str, Any]] | None = None
    try:
        prompt = _build_prompt(
            station_name, host_name, personality, news, commercial, character, tracks
        )
        raw = llm_client.complete_json(prompt, _LLM_SYSTEM_INSTRUCTION)
        script_json = _normalize_llm_script(raw)
    except Exception:  # noqa: BLE001 - never let LLM issues break generation
        script_json = None

    # 3. Procedural fallback.
    if script_json is None:
        script_json = _procedural_script(
            station, host_name, tracks, news, commercial, character
        )

    # 4. Derive caller memory summary from the produced script.
    caller_summary = character_agent.summarize_caller(station_name, script_json)
    character_id = character["id"] if character else None

    return {
        "title": title,
        "script_json": script_json,
        "character_id": character_id,
        "caller_summary": caller_summary,
        "track_ids": track_ids,
    }
