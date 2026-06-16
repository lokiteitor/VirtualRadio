"""Universe controller: owner-scoped aggregate counts across all resources.

Returns plain serializable data; the route wraps it in the response envelope.
"""
from __future__ import annotations

from app.models import (
    Character,
    Commercial,
    CommercialBrand,
    Episode,
    MusicTrack,
    NewsItem,
    Station,
    StoryEvent,
)
from app.repositories.base import scoped_query


def universe_summary() -> dict:
    """Return per-model counts scoped to the current user."""
    return {
        "stations": scoped_query(Station).count(),
        "episodes": scoped_query(Episode).count(),
        "news_items": scoped_query(NewsItem).count(),
        "brands": scoped_query(CommercialBrand).count(),
        "commercials": scoped_query(Commercial).count(),
        "characters": scoped_query(Character).count(),
        "music_tracks": scoped_query(MusicTrack).count(),
        "story_events": scoped_query(StoryEvent).count(),
    }
