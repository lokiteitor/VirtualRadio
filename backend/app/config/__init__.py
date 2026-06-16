"""Per-environment configuration for the VirtualRadio backend.

Configuration is driven entirely by environment variables (12-factor); secrets
and API keys are never hardcoded. Select the active config with FLASK_ENV
(development | testing | production).
"""
from __future__ import annotations

import os
from datetime import timedelta


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    API_VERSION = os.environ.get("API_VERSION", "1.0.0")
    API_PREFIX = "/api/v1"

    # --- JWT ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://virtualradio:virtualradio@db:5432/virtualradio",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Redis / Celery ---
    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    CELERY = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", REDIS_URL),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL),
        "task_track_started": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "result_expires": 3600,
        # Fail fast when publishing if the broker is unreachable, so a down Redis
        # never blocks the HTTP request that enqueues a job (it degrades gracefully).
        "broker_connection_retry_on_startup": True,
        "broker_connection_max_retries": 0,
        "broker_transport_options": {"socket_connect_timeout": 2, "socket_timeout": 2},
        "beat_schedule": {
            "cleanup-old-jobs": {
                "task": "tasks.cleanup_old_jobs",
                "schedule": 86400.0,  # daily
            },
            "archive-expired-news": {
                "task": "tasks.archive_expired_news",
                "schedule": 86400.0,  # daily
            },
        },
    }

    # --- Media volume ---
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/data/media")

    # --- CORS ---
    _origins = os.environ.get("CORS_ORIGINS", "*")
    CORS_ORIGINS = "*" if _origins.strip() == "*" else [
        o.strip() for o in _origins.split(",") if o.strip()
    ]

    # --- AI / TTS integrations ---
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")
    GEMINI_TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", 20))

    # Vertex AI (ADC) — alternative to GEMINI_API_KEY for the Gemini provider.
    # When true, the google-genai SDK uses Application Default Credentials with
    # GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION.
    GEMINI_USE_VERTEX = _bool(os.environ.get("GEMINI_USE_VERTEX"), default=False)
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

    # --- Maintenance ---
    JOBS_RETENTION_DAYS = int(os.environ.get("JOBS_RETENTION_DAYS", 7))

    # --- Logging ---
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    JSON_LOGS = _bool(os.environ.get("JSON_LOGS"), default=True)

    TESTING = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    JSON_LOGS = _bool(os.environ.get("JSON_LOGS"), default=False)


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://virtualradio:virtualradio@localhost:5432/virtualradio_test",
    )
    CELERY = {**BaseConfig.CELERY, "task_always_eager": True}


class ProductionConfig(BaseConfig):
    DEBUG = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return _CONFIGS.get(name, DevelopmentConfig)
