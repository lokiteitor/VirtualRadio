"""Episode routes: listing, retrieval, deletion, audio streaming and generation."""
from __future__ import annotations

from flask import Blueprint, request, send_file

from app.auth.permissions import check_permission
from app.common.responses import accepted, no_content, success
from app.controllers import episode as ctrl

bp = Blueprint("episodes", __name__)


@bp.get("/episodes")
@check_permission("episode", "read")
def list_episodes():
    station_id = request.args.get("station_id")
    data = ctrl.list_episodes(station_id)
    return success(data, {"count": len(data)})


@bp.get("/episodes/<episode_id>")
@check_permission("episode", "read")
def get_episode(episode_id):
    return success(ctrl.get_episode(episode_id))


@bp.post("/episodes/generate")
@check_permission("episode", "generate")
def generate_episode():
    return accepted(ctrl.generate_episode(request.get_json(silent=True)))


@bp.get("/episodes/<episode_id>/audio")
@check_permission("episode", "read")
def get_episode_audio(episode_id):
    abs_path = ctrl.get_episode_audio_path(episode_id)
    return send_file(abs_path, mimetype="audio/mpeg", conditional=True)


@bp.delete("/episodes/<episode_id>")
@check_permission("episode", "delete")
def delete_episode(episode_id):
    ctrl.delete_episode(episode_id)
    return no_content()
