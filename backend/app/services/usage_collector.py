"""Context-local collector for AI usage traces (LLM + TTS).

The generation worker opens a :func:`collect` context around the pipeline; the
LLM and TTS integration clients call :func:`record` for every call they make.
Using a :class:`contextvars.ContextVar` avoids threading a collector object
through ``build_episode`` → ``compile_episode`` → ``complete_json`` /
``get_tts_audio`` (module-level functions called deep in the stack).

:func:`record` is a no-op when there is no active context, so standalone calls to
the clients (smoke tests, suggestions) keep working unchanged. The worker reads
the collected dicts and persists them as ``GenerationTrace`` rows.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_current: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "usage_traces", default=None
)


@contextmanager
def collect():
    """Collect usage traces emitted by :func:`record` within this context.

    Yields the list that accumulates the trace dicts. Nested contexts each get
    their own list (the previous one is restored on exit).
    """
    token = _current.set([])
    try:
        yield _current.get()
    finally:
        _current.reset(token)


def record(
    kind: str,
    provider: str,
    *,
    model: str | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    total_tokens: int | None = None,
    cached: bool = False,
    latency_ms: int = 0,
) -> None:
    """Append one usage trace to the active context (no-op if none is active)."""
    bucket = _current.get()
    if bucket is None:
        return
    bucket.append(
        {
            "kind": kind,
            "provider": provider,
            "model": model,
            "tokens_in": tokens_in or 0,
            "tokens_out": tokens_out or 0,
            "total_tokens": (tokens_in or 0) + (tokens_out or 0)
            if total_tokens is None
            else total_tokens,
            "cached": cached,
            "latency_ms": latency_ms or 0,
        }
    )
