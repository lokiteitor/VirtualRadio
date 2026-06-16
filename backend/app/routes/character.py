"""Character routes: CRUD, AI suggestion and narrative memories."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import character as ctrl

bp = Blueprint("characters", __name__)


@bp.get("/characters")
@check_permission("character", "read")
def list_characters():
    data = ctrl.list_characters()
    return success(data, {"count": len(data)})


@bp.post("/characters")
@check_permission("character", "create")
def create_character():
    return created(ctrl.create_character(request.get_json(silent=True)))


@bp.post("/characters/suggest")
@check_permission("character", "suggest")
def suggest_character():
    return success(ctrl.suggest_character(request.get_json(silent=True)))


@bp.get("/characters/<character_id>")
@check_permission("character", "read")
def get_character(character_id):
    return success(ctrl.get_character(character_id))


@bp.put("/characters/<character_id>")
@check_permission("character", "update")
def update_character(character_id):
    return success(ctrl.update_character(character_id, request.get_json(silent=True)))


@bp.delete("/characters/<character_id>")
@check_permission("character", "delete")
def delete_character(character_id):
    ctrl.delete_character(character_id)
    return no_content()


@bp.get("/characters/<character_id>/memories")
@check_permission("character", "read_memories")
def list_character_memories(character_id):
    data = ctrl.list_character_memories(character_id)
    return success(data, {"count": len(data)})
