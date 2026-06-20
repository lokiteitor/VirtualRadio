"""Station routes.  Canonical template for CRUD-with-suggest resources."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import station as ctrl
from app.controllers import station_episode_settings as settings_ctrl
from app.controllers import station_music as music_ctrl

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


@bp.get("/stations/<station_id>/episode-settings")
@check_permission("station", "read_settings")
def get_episode_settings(station_id):
    return success(settings_ctrl.get_settings(station_id))


@bp.put("/stations/<station_id>/episode-settings")
@check_permission("station", "update_settings")
def update_episode_settings(station_id):
    return success(
        settings_ctrl.update_settings(station_id, request.get_json(silent=True))
    )


@bp.get("/stations/<station_id>/music")
@check_permission("station", "read_music")
def get_station_music(station_id):
    data = music_ctrl.get_station_music(station_id)
    return success(data, {"count": len(data)})


@bp.put("/stations/<station_id>/music")
@check_permission("station", "update_music")
def update_station_music(station_id):
    data = music_ctrl.set_station_music(station_id, request.get_json(silent=True))
    return success(data, {"count": len(data)})
