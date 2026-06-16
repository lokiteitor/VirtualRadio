"""pydub/FFmpeg audio production engine.

Ports the prototype's ``AudioProductionEngine`` to the backend. All paths are
resolved from ``MEDIA_ROOT`` (per-environment config / environment variable)
instead of a static directory. The layout under ``MEDIA_ROOT`` is::

    music/<owner_id>/   uploaded + synthesized chiptune tracks (per user)
    vox/                cached TTS speech clips
    fx/                 generated radio FX (sweeper)
    episodes/           exported episode MP3s

The module is import-safe: it performs no directory creation or network/DB
access at import time. ``tts_client`` is imported lazily inside
``compile_episode`` to avoid an import cycle.
"""
from __future__ import annotations

import logging
import os
import random
from typing import Callable

from pydub import AudioSegment
from pydub.generators import Sine, Triangle, WhiteNoise

logger = logging.getLogger(__name__)

# Synthesized track filenames generated when a user's music folder is empty.
_SYNTH_FILENAMES = ("synth_pastoral.mp3", "synth_highway.mp3", "synth_ambient.mp3")

# Chiptune track definitions ported verbatim from the prototype.
_SYNTH_TRACKS: tuple[dict, ...] = (
    {
        # Track 1: Country Farm Synth (slow chord progression) - C, F, G, C
        "filename": "synth_pastoral.mp3",
        "tempo": 110,
        "chords": [
            [261.63, 329.63, 392.00],
            [349.23, 440.00, 523.25],
            [392.00, 493.88, 587.33],
            [261.63, 329.63, 392.00],
        ],
        "melody": [392.00, 329.63, 349.23, 261.63, 293.66, 329.63, 392.00, 392.00],
        "duration_sec": 30,
    },
    {
        # Track 2: Highway Overdrive (faster driving bassline) - Am, G, F, G
        "filename": "synth_highway.mp3",
        "tempo": 140,
        "chords": [
            [220.00, 261.63, 329.63],
            [196.00, 246.94, 293.66],
            [174.61, 220.00, 261.63],
            [196.00, 246.94, 293.66],
        ],
        "melody": [220.00, 329.63, 220.00, 329.63, 293.66, 261.63, 246.94, 196.00],
        "duration_sec": 30,
    },
    {
        # Track 3: Conspiracy X-Files Ambient (slow mystery triangle waves) - Dm, Am, Dm, Em
        "filename": "synth_ambient.mp3",
        "tempo": 80,
        "chords": [
            [293.66, 349.23, 440.00],
            [220.00, 261.63, 329.63],
            [293.66, 349.23, 440.00],
            [329.63, 392.00, 493.88],
        ],
        "melody": [440.00, 523.25, 493.88, 392.00, 440.00, 349.23, 329.63, 293.66],
        "duration_sec": 35,
    },
)


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #
def _media_root() -> str:
    """Return ``MEDIA_ROOT`` from the Flask config, falling back to the env."""
    try:
        from flask import current_app

        if current_app:
            return current_app.config.get(
                "MEDIA_ROOT", os.environ.get("MEDIA_ROOT", "/data/media")
            )
    except Exception:  # pragma: no cover - outside app context
        pass
    return os.environ.get("MEDIA_ROOT", "/data/media")


def _fx_dir() -> str:
    return os.path.join(_media_root(), "fx")


def _vox_dir() -> str:
    return os.path.join(_media_root(), "vox")


def _episodes_dir() -> str:
    return os.path.join(_media_root(), "episodes")


def _music_dir(owner_id) -> str:
    return os.path.join(_media_root(), "music", str(owner_id))


def ensure_dirs(owner_id=None) -> None:
    """Create the shared asset folders (and the owner's music folder if given)."""
    paths = [_media_root(), _vox_dir(), _fx_dir(), _episodes_dir()]
    if owner_id is not None:
        paths.append(_music_dir(owner_id))
    for path in paths:
        os.makedirs(path, exist_ok=True)


# --------------------------------------------------------------------------- #
# FX asset generation
# --------------------------------------------------------------------------- #
def ensure_fx_assets() -> None:
    """Generate ``fx/sweeper.mp3`` if missing."""
    ensure_dirs()
    fx_dir = _fx_dir()
    sweeper_file = os.path.join(fx_dir, "sweeper.mp3")

    # Sweeper Sound (a futuristic synthesizer sweep — no white-noise blast).
    if not os.path.exists(sweeper_file):
        logger.info("Generating sweeper transition FX...")
        sweep = AudioSegment.silent(duration=1500)

        # Layer a fast pitch-shifting sine wave.
        for ms in range(0, 1000, 10):
            freq = 100 + (ms * 1.5)  # slanted pitch upward
            note = Sine(freq).to_audio_segment(duration=15, volume=-15)
            sweep = sweep.overlay(note, position=ms)

        sweep.export(sweeper_file, format="mp3")


# --------------------------------------------------------------------------- #
# Mock chiptune music generation
# --------------------------------------------------------------------------- #
def _generate_synth_track(
    file_path: str,
    tempo: int,
    chords: list[list[float]],
    melody: list[float],
    duration_sec: int,
) -> None:
    """Generate a chiptune-like song segment and export it as MP3."""
    beat_ms = int(60000 / tempo)
    num_beats = int((duration_sec * 1000) / beat_ms)

    # Background chord pads (Triangle waves for a softer tone).
    chord_track = AudioSegment.silent(duration=duration_sec * 1000)
    for beat in range(0, num_beats, 4):
        chord_notes = chords[(beat // 4) % len(chords)]
        pad = AudioSegment.silent(duration=beat_ms * 4)
        for freq in chord_notes:
            wave = Triangle(freq).to_audio_segment(duration=beat_ms * 4, volume=-22)
            pad = pad.overlay(wave)
        chord_track = chord_track.overlay(pad, position=beat * beat_ms)

    # Simple melody (Sine waves), a half note every 2 beats.
    melody_track = AudioSegment.silent(duration=duration_sec * 1000)
    for beat in range(num_beats):
        note_freq = melody[beat % len(melody)]
        if beat % 2 == 0:
            wave = (
                Sine(note_freq)
                .to_audio_segment(duration=beat_ms * 2 - 20, volume=-16)
                .fade_out(50)
            )
            melody_track = melody_track.overlay(wave, position=beat * beat_ms)

    mix = chord_track.overlay(melody_track)

    # Simple chiptune drum click (kick + snare) using Sine / WhiteNoise.
    drums = AudioSegment.silent(duration=duration_sec * 1000)
    for beat in range(num_beats):
        if beat % 4 == 0:  # kick
            click = Sine(60).to_audio_segment(duration=100, volume=-10).fade_out(80)
            drums = drums.overlay(click, position=beat * beat_ms)
        if beat % 4 == 2:  # snare click
            snare = WhiteNoise().to_audio_segment(duration=60, volume=-24).fade_out(40)
            drums = drums.overlay(snare, position=beat * beat_ms)

    final_mix = mix.overlay(drums).fade_out(1000)
    final_mix.export(file_path, format="mp3")


def generate_mock_music(owner_id) -> list[str]:
    """Synthesize 3 chiptune tracks into ``music/<owner_id>/`` if it has no MP3s.

    Returns the list of created file paths (empty if the folder already had
    music and nothing was generated).
    """
    ensure_dirs(owner_id)
    music_dir = _music_dir(owner_id)

    existing_mp3s = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
    if existing_mp3s:
        return []

    logger.info(
        "Music library empty for owner %s; generating chiptune mock tracks...",
        owner_id,
    )
    created: list[str] = []
    for track in _SYNTH_TRACKS:
        file_path = os.path.join(music_dir, track["filename"])
        _generate_synth_track(
            file_path=file_path,
            tempo=track["tempo"],
            chords=track["chords"],
            melody=track["melody"],
            duration_sec=track["duration_sec"],
        )
        created.append(file_path)

    return created


# --------------------------------------------------------------------------- #
# Episode compilation
# --------------------------------------------------------------------------- #
def compile_episode(
    episode,
    tracks: list,
    synth_fn: Callable[[str, str], AudioSegment],
) -> tuple[str, float]:
    """Compile an episode's script into a single exported MP3.

    Walks the episode's ``script_json`` segments (speech / music / fx), renders
    speech via ``synth_fn``, applies a telephony filter + crackle for phone
    calls (normal speech plays clean), slices and fades music with a sweeper
    transition, and appends sweeper FX. The final mix is normalized and
    exported to ``MEDIA_ROOT/episodes/<episode.id>.mp3``.

    Args:
        episode: the ``Episode`` model (uses ``.id`` and ``.script_json``).
        tracks: ordered list of the user's ``MusicTrack`` rows, used to resolve
            a music segment's ``track_id`` by index.
        synth_fn: callable ``(text, role) -> AudioSegment`` for speech synthesis
            (e.g. ``app.integrations.tts_client.get_tts_audio``).

    Returns:
        A ``(relative_audio_path, duration_seconds)`` tuple where the path is
        relative to ``MEDIA_ROOT`` (``"episodes/<episode.id>.mp3"``).
    """
    # Lazy import to avoid an import cycle between the engine and the TTS client.
    from app.integrations import tts_client

    ensure_dirs()
    ensure_fx_assets()

    script = episode.script_json or []

    # Load helper FX.
    sweeper = AudioSegment.from_file(os.path.join(_fx_dir(), "sweeper.mp3"))

    # Resolve music segment track_id by index into the user's ordered tracks.
    track_paths = [t.file_path for t in tracks]

    final_mix = AudioSegment.empty()

    logger.info("Compiling episode audio for: %s", getattr(episode, "title", episode.id))

    for segment in script:
        seg_type = segment.get("type")

        if seg_type == "speech":
            # Prefer an explicit configured voice (station/character/commercial);
            # fall back to the role alias ("host"/"reporter"/...).
            voice = segment.get("voice_name") or segment.get("voice_id") or "host"
            text = segment.get("text", "")

            # 1. Synthesize speech.
            vox_audio = synth_fn(text, voice)

            # 2. Apply telephony treatment for phone calls only: a bandpass so
            #    the call still sounds "phone-like", but no white-noise crackle.
            if segment.get("effect") == "telephony":
                vox_audio = tts_client.apply_telephony_filter(vox_audio)

            # Brief padding (300ms) at the end of speech.
            vox_audio += AudioSegment.silent(duration=300)
            final_mix += vox_audio

        elif seg_type == "music":
            # Resolve track path by planner index, with a random-owned fallback.
            track_idx = segment.get("track_id", 0)
            file_path = None

            if track_paths and track_idx is not None and 0 <= track_idx < len(track_paths):
                file_path = track_paths[track_idx]
            elif track_paths:
                file_path = random.choice(track_paths)

            if file_path and os.path.exists(file_path):
                song = AudioSegment.from_file(file_path)

                # Songs always play complete; just shape the edges.
                song = song.fade_in(1500).fade_out(2000)

                # Radio-style transition: overlay a sweeper at the start.
                song = song.overlay(sweeper.fade_out(500), position=0)

                final_mix += song + AudioSegment.silent(duration=500)
            else:
                # Silent fallback when no track is available.
                final_mix += AudioSegment.silent(duration=5000)

        elif seg_type == "fx":
            fx_name = segment.get("fx_type")
            if fx_name == "sweeper":
                final_mix += sweeper
            else:
                final_mix += AudioSegment.silent(duration=1000)

    # Global volume normalization for the simple chiptune / speech mix.
    final_mix = final_mix.normalize()

    # Export episode MP3 under MEDIA_ROOT/episodes/<episode.id>.mp3.
    relative_path = os.path.join("episodes", f"{episode.id}.mp3")
    output_path = os.path.join(_media_root(), relative_path)

    logger.info("Exporting final mix to %s...", output_path)
    final_mix.export(output_path, format="mp3")

    duration_sec = len(final_mix) / 1000.0
    logger.info(
        "Episode %s compiled successfully! Duration: %ss", episode.id, duration_sec
    )
    return relative_path, duration_sec
