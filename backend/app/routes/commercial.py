"""Commercial routes.  CRUD-with-suggest resource scoped to a brand."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import commercial as ctrl

bp = Blueprint("commercials", __name__)


@bp.get("/commercials")
@check_permission("commercial", "read")
def list_commercials():
    data = ctrl.list_commercials(request.args.get("brand_id"))
    return success(data, {"count": len(data)})


@bp.post("/commercials")
@check_permission("commercial", "create")
def create_commercial():
    return created(ctrl.create_commercial(request.get_json(silent=True)))


@bp.post("/commercials/suggest")
@check_permission("commercial", "suggest")
def suggest_commercial():
    return success(ctrl.suggest_commercial(request.get_json(silent=True)))


@bp.get("/commercials/<commercial_id>")
@check_permission("commercial", "read")
def get_commercial(commercial_id):
    return success(ctrl.get_commercial(commercial_id))


@bp.put("/commercials/<commercial_id>")
@check_permission("commercial", "update")
def update_commercial(commercial_id):
    return success(ctrl.update_commercial(commercial_id, request.get_json(silent=True)))


@bp.delete("/commercials/<commercial_id>")
@check_permission("commercial", "delete")
def delete_commercial(commercial_id):
    ctrl.delete_commercial(commercial_id)
    return no_content()
