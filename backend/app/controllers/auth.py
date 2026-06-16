"""Authentication controller: register, login, refresh."""
from __future__ import annotations

from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import func

from app.common.errors import ConflictError, UnauthorizedError
from app.extensions import db
from app.models import User
from app.schemas.auth import login_schema, register_schema, user_schema
from app.schemas.common import load_or_422
from app.seeds.universe import seed_default_universe


def _tokens_for(user: User) -> dict:
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
        "user": user_schema.dump(user),
    }


def register(payload) -> dict:
    data = load_or_422(register_schema, payload)
    email = data["email"].strip().lower()

    exists = db.session.query(User.id).filter(func.lower(User.email) == email).first()
    if exists:
        raise ConflictError("El email ya está registrado", code="EMAIL_TAKEN")

    user = User(email=email, display_name=data.get("display_name"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()  # assign user.id before seeding

    seed_default_universe(user.id)
    db.session.commit()

    return _tokens_for(user)


def login(payload) -> dict:
    data = load_or_422(login_schema, payload)
    email = data["email"].strip().lower()

    user = db.session.query(User).filter(func.lower(User.email) == email).first()
    if user is None or not user.check_password(data["password"]):
        raise UnauthorizedError("Credenciales inválidas")
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")

    return _tokens_for(user)


def refresh(identity: str) -> dict:
    return {"access_token": create_access_token(identity=str(identity))}
