"""Universe routes: aggregate summary of the current user's resources."""
from __future__ import annotations

from flask import Blueprint

from app.auth.permissions import check_permission
from app.common.responses import success
from app.controllers import universe as ctrl

bp = Blueprint("universe", __name__)


@bp.get("/universe/summary")
@check_permission("universe", "read")
def universe_summary():
    return success(ctrl.universe_summary())
