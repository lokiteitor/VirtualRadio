"""Commercial brand routes (CRUD-with-suggest)."""
from __future__ import annotations

from flask import Blueprint, request

from app.auth.permissions import check_permission
from app.common.responses import created, no_content, success
from app.controllers import brand as ctrl

bp = Blueprint("brands", __name__)


@bp.get("/brands")
@check_permission("brand", "read")
def list_brands():
    data = ctrl.list_brands()
    return success(data, {"count": len(data)})


@bp.post("/brands")
@check_permission("brand", "create")
def create_brand():
    return created(ctrl.create_brand(request.get_json(silent=True)))


@bp.post("/brands/suggest")
@check_permission("brand", "suggest")
def suggest_brand():
    return success(ctrl.suggest_brand(request.get_json(silent=True)))


@bp.get("/brands/<brand_id>")
@check_permission("brand", "read")
def get_brand(brand_id):
    return success(ctrl.get_brand(brand_id))


@bp.put("/brands/<brand_id>")
@check_permission("brand", "update")
def update_brand(brand_id):
    return success(ctrl.update_brand(brand_id, request.get_json(silent=True)))


@bp.delete("/brands/<brand_id>")
@check_permission("brand", "delete")
def delete_brand(brand_id):
    ctrl.delete_brand(brand_id)
    return no_content()
