"""SQLAlchemy models package.

Importing this module registers every model on the shared metadata, which is
required for migrations and ``db.create_all()``.
"""
from app.models.character import Character
from app.models.character_memory import CharacterMemory
from app.models.commercial import Commercial
from app.models.commercial_brand import CommercialBrand
from app.models.enums import (
    JobStatus,
    NewsCategory,
    NewsTone,
    SegmentType,
    StoryStatus,
    TraceKind,
)
from app.models.episode import Episode
from app.models.generation_job import GenerationJob
from app.models.generation_trace import GenerationTrace
from app.models.music_track import MusicTrack
from app.models.news_item import NewsItem
from app.models.role import Role
from app.models.station import Station
from app.models.station_episode_settings import StationEpisodeSettings
from app.models.station_music import StationMusic
from app.models.station_news_read import StationNewsRead
from app.models.story_event import StoryEvent
from app.models.user import User

__all__ = [
    "User",
    "Role",
    "Station",
    "StationEpisodeSettings",
    "StationMusic",
    "StationNewsRead",
    "Episode",
    "MusicTrack",
    "NewsItem",
    "CommercialBrand",
    "Commercial",
    "Character",
    "CharacterMemory",
    "StoryEvent",
    "GenerationJob",
    "GenerationTrace",
    "NewsCategory",
    "NewsTone",
    "StoryStatus",
    "JobStatus",
    "TraceKind",
    "SegmentType",
]
