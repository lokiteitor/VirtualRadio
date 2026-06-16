"""Domain enums, mapped to native PostgreSQL ENUM types."""
from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


class NewsCategory(str, enum.Enum):
    AGRICULTURA = "Agricultura"
    TRANSPORTE = "Transporte"
    ECONOMIA = "Economía"
    TECNOLOGIA = "Tecnología"
    CLIMA = "Clima"
    COMUNIDAD = "Comunidad"
    POLITICA_LOCAL = "Política Local"
    SUCESOS_EXTRANOS = "Sucesos Extraños"


class NewsTone(str, enum.Enum):
    SERIO = "Serio"
    SENSACIONALISTA = "Sensacionalista"
    MISTERIOSO = "Misterioso"
    ABSURDO = "Absurdo"


class StoryStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    SYNTHESIZING = "synthesizing"
    MIXING = "mixing"
    COMPLETED = "completed"
    FAILED = "failed"


class SegmentType(str, enum.Enum):
    """Script segment type (validation only; ``script_json`` is stored as JSONB)."""

    SPEECH = "speech"
    MUSIC = "music"
    FX = "fx"


class Language(str, enum.Enum):
    """Script language for a station's generated episodes."""

    SPANISH = "es"
    ENGLISH = "en"


def pg_enum(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """Build a native PostgreSQL ENUM whose values are the enum *values*."""
    return SAEnum(
        py_enum,
        name=name,
        values_callable=lambda e: [member.value for member in e],
        native_enum=True,
    )


# Stable type names shared between models and the Alembic migration.
NEWS_CATEGORY_ENUM_NAME = "news_category"
NEWS_TONE_ENUM_NAME = "news_tone"
STORY_STATUS_ENUM_NAME = "story_status"
JOB_STATUS_ENUM_NAME = "job_status"
LANGUAGE_ENUM_NAME = "language"
