"""News routes.  CRUD-with-suggest resource over the shared news library."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import news as ctrl
from app.models.enums import NewsCategory

bp = Blueprint("news", __name__)


def _parse_bool(value):
    if value is None:
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_category(value):
    if value is None:
        return None
    try:
        return NewsCategory(value)
    except ValueError:
        return None


@bp.get("/news")
@check_permission("news", "read")
def list_news():
    is_active = _parse_bool(request.args.get("is_active"))
    category = _parse_category(request.args.get("category"))
    data = ctrl.list_news(is_active=is_active, category=category)
    return success(data, {"count": len(data)})


@bp.post("/news")
@check_permission("news", "create")
def create_news():
    return created(ctrl.create_news(request.get_json(silent=True)))


@bp.post("/news/suggest")
@check_permission("news", "suggest")
def suggest_news():
    return success(ctrl.suggest_news(request.get_json(silent=True)))


@bp.get("/news/<news_id>")
@check_permission("news", "read")
def get_news(news_id):
    return success(ctrl.get_news(news_id))


@bp.put("/news/<news_id>")
@check_permission("news", "update")
def update_news(news_id):
    return success(ctrl.update_news(news_id, request.get_json(silent=True)))


@bp.delete("/news/<news_id>")
@check_permission("news", "delete")
def delete_news(news_id):
    ctrl.delete_news(news_id)
    return no_content()
