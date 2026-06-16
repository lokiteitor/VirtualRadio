"""Story event routes.  CRUD resource (no suggest endpoint)."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.errors import ValidationFailedError
from app.common.responses import created, no_content, success
from app.controllers import story_event as ctrl
from app.models.enums import StoryStatus

bp = Blueprint("story_events", __name__)


def _parse_status(raw: str | None) -> StoryStatus | None:
    if raw is None:
        return None
    try:
        return StoryStatus(raw)
    except ValueError as exc:
        raise ValidationFailedError(
            details={"status": [f"Invalid value '{raw}'."]}
        ) from exc


@bp.get("/story-events")
@check_permission("story_event", "read")
def list_story_events():
    status = _parse_status(request.args.get("status"))
    data = ctrl.list_story_events(status)
    return success(data, {"count": len(data)})


@bp.post("/story-events")
@check_permission("story_event", "create")
def create_story_event():
    return created(ctrl.create_story_event(request.get_json(silent=True)))


@bp.get("/story-events/<event_id>")
@check_permission("story_event", "read")
def get_story_event(event_id):
    return success(ctrl.get_story_event(event_id))


@bp.put("/story-events/<event_id>")
@check_permission("story_event", "update")
def update_story_event(event_id):
    return success(ctrl.update_story_event(event_id, request.get_json(silent=True)))


@bp.delete("/story-events/<event_id>")
@check_permission("story_event", "delete")
def delete_story_event(event_id):
    ctrl.delete_story_event(event_id)
    return no_content()
