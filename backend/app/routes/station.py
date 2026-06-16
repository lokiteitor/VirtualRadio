"""Station routes.  Canonical template for CRUD-with-suggest resources."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import station as ctrl

bp = Blueprint("stations", __name__)


@bp.get("/stations")
@check_permission("station", "read")
def list_stations():
    data = ctrl.list_stations()
    return success(data, {"count": len(data)})


@bp.post("/stations")
@check_permission("station", "create")
def create_station():
    return created(ctrl.create_station(request.get_json(silent=True)))


@bp.post("/stations/suggest")
@check_permission("station", "suggest")
def suggest_station():
    return success(ctrl.suggest_station(request.get_json(silent=True)))


@bp.get("/stations/<station_id>")
@check_permission("station", "read")
def get_station(station_id):
    return success(ctrl.get_station(station_id))


@bp.put("/stations/<station_id>")
@check_permission("station", "update")
def update_station(station_id):
    return success(ctrl.update_station(station_id, request.get_json(silent=True)))


@bp.delete("/stations/<station_id>")
@check_permission("station", "delete")
def delete_station(station_id):
    ctrl.delete_station(station_id)
    return no_content()
