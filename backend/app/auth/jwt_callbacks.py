"""Flask-JWT-Extended callbacks: identity loading and error envelopes."""
from __future__ import annotations

import uuid

from flask import jsonify
from flask_jwt_extended import JWTManager

from app.extensions import db


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message, "details": {}}}), status


def register_jwt_callbacks(jwt: JWTManager) -> None:
    @jwt.user_lookup_loader
    def _load_user(_jwt_header, jwt_data):
        from app.models import User  # local import to avoid circular import

        identity = jwt_data.get("sub")
        if not identity:
            return None
        try:
            user_id = uuid.UUID(str(identity))
        except (ValueError, TypeError):
            return None
        return db.session.get(User, user_id)

    @jwt.unauthorized_loader
    def _unauthorized(_reason):
        return _error("UNAUTHORIZED", "Token inválido o ausente", 401)

    @jwt.invalid_token_loader
    def _invalid(_reason):
        return _error("UNAUTHORIZED", "Token inválido o ausente", 401)

    @jwt.expired_token_loader
    def _expired(_header, _payload):
        return _error("UNAUTHORIZED", "Token expirado", 401)

    @jwt.revoked_token_loader
    def _revoked(_header, _payload):
        return _error("UNAUTHORIZED", "Token revocado", 401)

    @jwt.needs_fresh_token_loader
    def _needs_fresh(_header, _payload):
        return _error("UNAUTHORIZED", "Se requiere un token fresco", 401)
