"""Public healthcheck route."""
from __future__ import annotations

from flask import Blueprint, current_app

from app.common.responses import success

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return success(
        {"status": "ok", "version": current_app.config.get("API_VERSION", "1.0.0")}
    )
