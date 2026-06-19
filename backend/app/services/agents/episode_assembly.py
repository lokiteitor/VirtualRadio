"""Episode assembly orchestrator.

``build_episode`` is the single entry point used by the generation task. It:

1. Asks :mod:`episode_planner` to pick the owner-scoped content elements
   (lists of tracks, news, commercials and callers, sized by the station's
   :class:`StationEpisodeSettings`).
2. Tries the LLM (:func:`app.integrations.llm_client.complete_json`) with a
   count-aware prompt for a full script.
3. On ``None`` / invalid output, builds the script procedurally with a radio-like
   block layout: the host hands off to a block of **at least 3 back-to-back
   songs**, the commercials for that break play on their own (the host never
   mentions them), then the host returns. The caller phone-ins are spread across
   the whole show, not clustered.

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
# ``voice_name`` is an optional explicit Gemini voice that overrides the role
# voice (set per commercial/character/station; see ``_assign_voices``).
_SEGMENT_KEYS = (
    "type", "speaker", "text", "voice_id", "voice_name", "effect", "track_id", "duration_seconds",
)

_LLM_SYSTEM_INSTRUCTION = (
    "You are a professional script writer for a satirical radio generator. You write "
    "funny, immersive radio scripts and output them strictly in JSON format."
)

# Human-readable language names for the LLM directive, keyed by the stored code.
_LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}


# --------------------------------------------------------------------------- #
# Layout: a radio-like block plan (music blocks + ad breaks + talk slots)
# --------------------------------------------------------------------------- #
# At least this many songs play back-to-back per music block (when available).
_SONGS_PER_BLOCK = 3


def _talk_queue(news_count: int, caller_count: int) -> list[tuple[str, int]]:
    """Round-robin interleave of news + callers so the two alternate, not clump.

    Commercials are NOT part of the talk stream: they play in their own break
    after each music block and the host never introduces them. Each type keeps
    its internal order (caller ``idx`` 0, 1, 2, ...), which ``summarize_caller``
    relies on for caller/index alignment.
    """
    counters = {"news": 0, "caller": 0}
    remaining = {"news": news_count, "caller": caller_count}
    order: list[tuple[str, int]] = []
    while any(v > 0 for v in remaining.values()):
        for kind in ("news", "caller"):
            if remaining[kind] > 0:
                order.append((kind, counters[kind]))
                counters[kind] += 1
                remaining[kind] -= 1
    return order


def _even_chunks(total: int, groups: int, *, heavy_last: bool = False) -> list[int]:
    """Split ``total`` into ``groups`` non-negative sizes differing by at most 1.

    With ``heavy_last`` the larger (remainder) groups are placed at the end
    instead of the start. Returns ``[]`` when ``groups <= 0``.
    """
    if groups <= 0:
        return []
    base, extra = divmod(max(0, total), groups)
    if heavy_last:
        return [base + (1 if i >= groups - extra else 0) for i in range(groups)]
    return [base + (1 if i < extra else 0) for i in range(groups)]


def _split_contiguous(items: list, groups: int, *, heavy_last: bool = False) -> list[list]:
    """Slice ``items`` into ``groups`` contiguous sublists (order preserved)."""
    out: list[list] = []
    pos = 0
    for size in _even_chunks(len(items), groups, heavy_last=heavy_last):
        out.append(items[pos:pos + size])
        pos += size
    return out


def _distribute_commercials(commercial_count: int, blocks: int) -> list[list[int]]:
    """Assign commercial indices to one ad break after each of ``blocks`` blocks.

    Each break gets at least one ad by recycling the available commercials when
    there are fewer commercials than blocks (per "comercial tras cada bloque").
    ``commercial_count == 0`` is respected as "no commercials" (empty breaks).
    """
    if blocks <= 0:
        return []
    if commercial_count <= 0:
        return [[] for _ in range(blocks)]
    # Recycle so every break has >= 1 ad; when there are more ads than breaks,
    # use each ad once and spread them across the breaks.
    seq = [i % commercial_count for i in range(max(commercial_count, blocks))]
    return _split_contiguous(seq, blocks)


def _plan_blocks(
    song_count: int, news_count: int, commercial_count: int, caller_count: int
) -> dict[str, Any]:
    """Structural plan for the episode, driven by the song count.

    Returns ``{"blocks", "breaks", "talk"}`` where ``blocks`` is a list of music
    blocks (each a list of GLOBAL song indices, all >= 3 when ``song_count >= 3``),
    ``breaks`` is the per-block list of commercial indices, and ``talk`` is the
    list of talk-item groups for the host-talk slots. With ``B`` music blocks
    there are ``B + 1`` talk slots (intro side, between blocks, outro side).

    ``song_count == 0`` collapses to a talk-only show: one talk stream and a
    single consolidated ad break (rendered just before the outro).
    """
    talk = _talk_queue(news_count, caller_count)

    if song_count <= 0:
        return {
            "blocks": [],
            "breaks": [list(range(commercial_count))] if commercial_count > 0 else [],
            "talk": [talk],
        }

    blocks_count = max(1, song_count // _SONGS_PER_BLOCK)
    blocks: list[list[int]] = []
    pos = 0
    for size in _even_chunks(song_count, blocks_count):
        blocks.append(list(range(pos, pos + size)))
        pos += size

    return {
        "blocks": blocks,
        "breaks": _distribute_commercials(commercial_count, blocks_count),
        "talk": _split_contiguous(talk, blocks_count + 1),
    }


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
        4. Play {song_count} songs (Music segments):
{songs_block}

        Structure the show like real radio, following these rules strictly:
        - Group the songs into blocks of AT LEAST 3 consecutive Music segments. Within a block the
          songs play back-to-back: the Host introduces the block ONCE (before the first song) and
          does NOT speak again until the block ends.
        - After each music block, place that break's Commercial segments (read by "Commercial_Voice").
          The Host must NEVER mention, introduce, tease, comment on, or thank the commercials — he
          hands off to music and the ads simply run; after the ads the Host returns with talk.
        - Spread the caller phone-ins across the WHOLE show: never two callers back-to-back, and not
          all clustered at the start or end.
        - "Reporter" segments MUST NOT mention or reference the station name in their "text"; the
          reporter only narrates the news story itself (this keeps the reporter audio reusable across
          stations). The station identity is carried by the Host's surrounding talk, not the reporter.
        - Open with a short Host greeting and close with a short Host goodbye.

        Generate the output strictly as a JSON list of segments. Do not include markdown code block formatting like ```json ... ```, just the raw JSON.
        Each segment must have:
        - "type": "speech", "music", or "fx"
        - "speaker": "Host", "Caller", "Reporter", "Commercial_Voice", or null (for music/fx)
        - "text": The spoken text or script, or song title for music
        - "voice_id": "host", "caller", "reporter", "commercial", or null
        - "effect": "telephony" (for callers), "ducking" (for speech during music), or null
        - "track_id": The song's index (0..{max(song_count - 1, 0)}) in the song list above if type is music, otherwise null.
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
    """Build a satirical, radio-like script procedurally for arbitrary counts.

    Structure (see :func:`_plan_blocks`): intro greeting, then for each music
    block a single host tee, the block's songs back-to-back, the block's ad
    break (no host), and the host returning with talk. Callers are spread across
    the talk slots; the host never mentions the commercials.
    """
    station_name = getattr(station, "name", "WCTR Sim Edition")
    plan = _plan_blocks(len(tracks), len(news_items), len(commercials), len(characters))
    blocks = plan["blocks"]
    breaks = plan["breaks"]
    talk_slots = plan["talk"]

    segments: list[dict[str, Any]] = [host_agent.intro_segment(station)]
    prev_artist: str | None = None  # None until the first song plays (opening variant)

    def emit_talk(items: list[tuple[str, int]]) -> None:
        # Reads the enclosing ``prev_artist`` at call time so news transitions
        # reference the song that just played (or the opening variant when None).
        for kind, idx in items:
            if kind == "news":
                segments.extend(
                    news_agent.build_segments(station_name, host_name, news_items[idx], prev_artist)
                )
            elif kind == "caller":
                character = characters[idx] if idx < len(characters) else None
                segments.extend(character_agent.build_segments(host_name, character))

    # Talk-only show (no songs configured): all talk, then a single ad break.
    if not blocks:
        emit_talk(talk_slots[0])
        for ci in (breaks[0] if breaks else []):
            segments.extend(commercial_agent.build_segments(commercials[ci]))
        segments.append(host_agent.outro_segment(station))
        return segments

    emit_talk(talk_slots[0])
    for k, block in enumerate(blocks):
        # Single host tee for the whole block; songs then play back-to-back.
        segments.append(host_agent.music_tee_segment(tracks[block[0]], opening=(k == 0)))
        for gi in block:
            segments.append(host_agent.music_segment(tracks[gi], gi))
            prev_artist = tracks[gi]["artist"]
        # Ad break (host stays silent — never introduces the commercials).
        for ci in breaks[k]:
            segments.extend(commercial_agent.build_segments(commercials[ci]))
        # Host returns with the next talk slot (news/callers).
        emit_talk(talk_slots[k + 1])

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
# Voice assignment (configurable per station host/reporter and per character)
# --------------------------------------------------------------------------- #
def _assign_voices(
    script: list[dict[str, Any]],
    host_voice: str | None,
    reporter_voice: str | None,
    characters: list[dict[str, Any] | None],
) -> None:
    """Fill each speech segment's ``voice_name`` from the configured voices.

    Applies to both the procedural and LLM scripts. Host/reporter voices are
    per-station (assigned by role); caller voices are per-character (assigned by
    caller order, which mirrors :func:`character_agent.summarize_caller`).
    Commercial voices are set per commercial by the commercial agent, so a
    segment that already carries a ``voice_name`` is left untouched. Nothing is
    set when the resolved voice is ``None`` (the role default then applies).
    """
    caller_voices = [c.get("voice") if c else None for c in characters]
    caller_i = 0
    for segment in script:
        is_caller = segment.get("speaker") == "Caller"
        if not segment.get("voice_name"):
            if is_caller:
                cv = caller_voices[caller_i] if caller_i < len(caller_voices) else None
                if cv:
                    segment["voice_name"] = cv
            elif segment.get("voice_id") == "host" and host_voice:
                segment["voice_name"] = host_voice
            elif segment.get("voice_id") == "reporter" and reporter_voice:
                segment["voice_name"] = reporter_voice
        if is_caller:
            caller_i += 1


def _voice_value(station, attr: str) -> str | None:
    """Read a station voice attribute as a plain Gemini voice name (or None)."""
    voice = getattr(station, attr, None)
    return voice.value if hasattr(voice, "value") else voice


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

    # Real NewsItem ids used this episode (the worker records them so each news is
    # read once per station; procedural fallbacks, if any, have id=None).
    news_ids: list[uuid.UUID] = [n["id"] for n in news_items if n.get("id") is not None]

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

    # 3b. Apply the configurable voices (station host/reporter + per-character).
    _assign_voices(
        script_json,
        _voice_value(station, "host_voice"),
        _voice_value(station, "reporter_voice"),
        characters,
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
        "news_ids": news_ids,
    }
