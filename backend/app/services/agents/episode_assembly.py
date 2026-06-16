"""Episode assembly orchestrator.

``build_episode`` is the single entry point used by the generation task. It:

1. Asks :mod:`episode_planner` to pick the owner-scoped content elements
   (lists of tracks, news, commercials and callers, sized by the station's
   :class:`StationEpisodeSettings`).
2. Tries the LLM (:func:`app.integrations.llm_client.complete_json`) with a
   count-aware prompt for a full script.
3. On ``None`` / invalid output, builds the script procedurally via a
   deterministic layout that interleaves songs with the news / commercial /
   caller blocks.

Either way it returns the pinned dict::

    {
        "title": str,
        "script_json": list[segment dict],
        "callers": list[{"character_id": UUID, "caller_summary": str | None}],
        "track_ids": list[UUID],   # ordered selected MusicTrack ids
    }

Music segments use ``track_id = index into the ordered track list``.

The module is import-safe: it performs no network/DB access at import time and
imports the LLM client lazily inside :func:`build_episode`.
"""
from __future__ import annotations

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

# Human-readable language names for the LLM directive, keyed by the stored code.
_LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}


# --------------------------------------------------------------------------- #
# Layout: where each block goes (shared by the procedural + LLM descriptions)
# --------------------------------------------------------------------------- #
def _talk_queue(news_count: int, commercial_count: int, caller_count: int) -> list[tuple[str, int]]:
    """Round-robin interleave of the talk blocks so types alternate, not clump."""
    counters = {"news": 0, "commercial": 0, "caller": 0}
    remaining = {"news": news_count, "commercial": commercial_count, "caller": caller_count}
    order: list[tuple[str, int]] = []
    while any(v > 0 for v in remaining.values()):
        for kind in ("news", "commercial", "caller"):
            if remaining[kind] > 0:
                order.append((kind, counters[kind]))
                counters[kind] += 1
                remaining[kind] -= 1
    return order


def _layout(
    song_count: int, news_count: int, commercial_count: int, caller_count: int
) -> list[tuple[str, int]]:
    """Ordered ``(kind, idx)`` blocks for an episode of arbitrary counts.

    ``intro`` first, ``outro`` last; the body starts with a song (the intro
    teases song 0) and alternates song / talk-block, draining whichever queue
    still has items. Coherent for any counts, including zeros.
    """
    layout: list[tuple[str, int]] = [("intro", 0)]
    songs = [("song", i) for i in range(max(0, song_count))]
    talk = _talk_queue(news_count, commercial_count, caller_count)

    si = ti = 0
    take_song = True
    while si < len(songs) or ti < len(talk):
        if take_song and si < len(songs):
            layout.append(songs[si]); si += 1
        elif not take_song and ti < len(talk):
            layout.append(talk[ti]); ti += 1
        elif si < len(songs):
            layout.append(songs[si]); si += 1
        else:
            layout.append(talk[ti]); ti += 1
        take_song = not take_song

    layout.append(("outro", 0))
    return layout


# --------------------------------------------------------------------------- #
# LLM prompt (count-aware)
# --------------------------------------------------------------------------- #
def _build_prompt(
    station_name: str,
    host_name: str,
    personality: str,
    news_items: list[dict[str, Any]],
    commercials: list[dict[str, Any]],
    characters: list[dict[str, Any] | None],
    tracks: list[dict[str, Any]],
    language: str = "es",
) -> str:
    song_count = len(tracks)
    caller_count = len(characters)
    language_name = _LANGUAGE_NAMES.get(language, "Spanish")

    songs_block = "\n".join(
        f'        - Song {i}: "{t["title"]}" by {t["artist"]}' for i, t in enumerate(tracks)
    ) or "        - (no songs this episode)"
    news_block = "\n".join(
        f'        - News {i}: Headline "{n.get("headline", "")}". Summary "{n.get("summary", "")}".'
        for i, n in enumerate(news_items)
    ) or "        - (no news this episode)"
    commercial_block = "\n".join(
        f'        - Commercial {i}: Brand "{c.get("brand_name", "")}". Script "{c.get("script", "")}".'
        for i, c in enumerate(commercials)
    ) or "        - (no commercials this episode)"
    caller_block = "\n".join(
        _describe_caller(i, c) for i, c in enumerate(characters)
    ) or "        - (no callers this episode)"

    return f"""
        Generate a complete audio show script for the fictional radio station "{station_name}".
        Host Name: {host_name}
        Host Personality: {personality}

        IMPORTANT: Write ALL spoken content (every "text" field) strictly in {language_name}.

        Build the show from these content elements (use ALL of them):
        1. News items ({len(news_items)}). Present each with the station's characteristic tone:
{news_block}
        2. Commercials ({len(commercials)}). Read each sponsor script:
{commercial_block}
        3. Caller interactions ({caller_count}). Create a funny phone dialogue for each caller
           (they should reference their memories where given); the host responds:
{caller_block}
        4. Play {song_count} songs (Music segments). Introduce each song:
{songs_block}

        Interleave the songs with the talk blocks so the show flows like real radio.
        Generate the output strictly as a JSON list of segments. Do not include markdown code block formatting like ```json ... ```, just the raw JSON.
        Each segment must have:
        - "type": "speech", "music", or "fx"
        - "speaker": "Host", "Caller", "Reporter", "Commercial_Voice", or null (for music/fx)
        - "text": The spoken text or script, or song title for music
        - "voice_id": "host", "caller", "reporter", "commercial", or null
        - "effect": "telephony" (for callers), "ducking" (for speech during music), or null
        - "track_id": The song index (0..{max(song_count - 1, 0)}) if type is music, otherwise null.
        - "duration_seconds": estimate duration (speech ~ 150 words per minute).
        """


def _describe_caller(index: int, character: dict[str, Any] | None) -> str:
    if not character:
        return f"        - Caller {index}: an anonymous excited listener (invent a fun call)."
    memories = character.get("memories") or "None"
    return (
        f'        - Caller {index}: Name {character.get("name", "Anon")}; '
        f'Role {character.get("description", "A listener")}; '
        f'Personality {character.get("personality", "Excited")}; Memories {memories}.'
    )


# --------------------------------------------------------------------------- #
# Procedural script (deterministic layout over the agent builders)
# --------------------------------------------------------------------------- #
def _procedural_script(
    station,
    host_name: str,
    tracks: list[dict[str, Any]],
    news_items: list[dict[str, Any]],
    commercials: list[dict[str, Any]],
    characters: list[dict[str, Any] | None],
) -> list[dict[str, Any]]:
    """Build a satirical script procedurally for arbitrary counts."""
    station_name = getattr(station, "name", "WCTR Sim Edition")
    layout = _layout(len(tracks), len(news_items), len(commercials), len(characters))

    segments: list[dict[str, Any]] = []
    prev_artist = tracks[0]["artist"] if tracks else "la música"

    for kind, idx in layout:
        if kind == "intro":
            segments.append(host_agent.intro_segment(station, tracks[0] if tracks else None))
        elif kind == "song":
            track = tracks[idx]
            if idx > 0:  # song 0 is teased by the intro
                variant = "last" if idx == len(tracks) - 1 else "relax"
                segments.append(host_agent.song_intro_segment(track, variant=variant))
            segments.append(host_agent.music_segment(track, idx))
            prev_artist = track["artist"]
        elif kind == "news":
            segments.extend(
                news_agent.build_segments(station_name, host_name, news_items[idx], prev_artist)
            )
        elif kind == "commercial":
            segments.extend(commercial_agent.build_segments(commercials[idx]))
        elif kind == "caller":
            character = characters[idx] if idx < len(characters) else None
            segments.extend(character_agent.build_segments(host_name, character))
        elif kind == "outro":
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
def build_episode(owner_id: uuid.UUID, station, settings) -> dict[str, Any]:
    """Orchestrate the agents and return the pinned episode-assembly dict."""
    from app.integrations import llm_client

    station_name = getattr(station, "name", "WCTR Sim Edition")
    host_name = getattr(station, "host_name", None) or "el Locutor"
    personality = getattr(station, "personality", None) or ""

    # 1. Plan the content elements (owner-scoped, sized by the station settings).
    plan = episode_planner.plan_episode(owner_id, station, settings)
    tracks = plan["tracks"]
    news_items = plan["news"]
    commercials = plan["commercials"]
    characters = plan["characters"]

    # Ordered selected MusicTrack ids (only real DB rows; fallback tracks have id=None).
    track_ids: list[uuid.UUID] = [t["id"] for t in tracks if t.get("id") is not None]

    # Base title; the generation worker overrides it with the deterministic
    # per-station number ("<station> - Episodio N").
    title = station_name

    # Configured script language ("es" / "en"); drives the LLM directive and the
    # procedural fallback's hardcoded copy.
    language = episode_planner.language_code(settings)

    # 2. Try the LLM first.
    script_json: list[dict[str, Any]] | None = None
    try:
        prompt = _build_prompt(
            station_name, host_name, personality, news_items, commercials, characters,
            tracks, language,
        )
        raw = llm_client.complete_json(prompt, _LLM_SYSTEM_INSTRUCTION)
        script_json = _normalize_llm_script(raw)
    except Exception:  # noqa: BLE001 - never let LLM issues break generation
        script_json = None

    # 3. Procedural fallback (Spanish copy; language only drives the LLM path).
    if script_json is None:
        script_json = _procedural_script(
            station, host_name, tracks, news_items, commercials, characters
        )

    # 4. Derive a caller-memory summary for each real character (in caller order).
    real_characters = [c for c in characters if c and c.get("id") is not None]
    callers = [
        {
            "character_id": c["id"],
            "caller_summary": character_agent.summarize_caller(station_name, script_json, index=i),
        }
        for i, c in enumerate(real_characters)
    ]

    return {
        "title": title,
        "script_json": script_json,
        "callers": callers,
        "track_ids": track_ids,
    }
