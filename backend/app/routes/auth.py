"""Authentication routes (public, except refresh which needs a refresh token)."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.common.responses import created, success
from app.controllers import auth as ctrl

bp = Blueprint("auth", __name__)


@bp.post("/auth/register")
def register():
    return created(ctrl.register(request.get_json(silent=True)))


@bp.post("/auth/login")
def login():
    return success(ctrl.login(request.get_json(silent=True)))


@bp.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    return success(ctrl.refresh(get_jwt_identity()))
