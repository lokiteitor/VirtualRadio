"""Music library routes."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import music as ctrl

bp = Blueprint("music", __name__)


@bp.get("/music")
@check_permission("music", "read")
def list_music():
    data = ctrl.list_music()
    total_duration = sum((item.get("duration") or 0) for item in data)
    return success(data, {"count": len(data), "total_duration": total_duration})


@bp.post("/music/upload")
@check_permission("music", "upload")
def upload_music():
    return created(ctrl.upload_music(request.files.get("file")))


@bp.post("/music/scan")
@check_permission("music", "scan")
def scan_music():
    return success(ctrl.scan_music())


@bp.delete("/music/<music_id>")
@check_permission("music", "delete")
def delete_music(music_id):
    ctrl.delete_music(music_id)
    return no_content()
