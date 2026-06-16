"""Seed the RBAC role catalog (idempotent)."""
from __future__ import annotations

from app.auth.permissions import USER_PERMISSIONS
from app.extensions import db
from app.models import Role

_ROLES = [
    {
        "code": "USER",
        "name": "Usuario",
        "description": (
            "Usuario propietario de su propio universo de datos. "
            "Acceso exclusivo a sus recursos (scope own)."
        ),
        "is_system_role": True,
        "permissions": sorted(USER_PERMISSIONS),
    },
    {
        "code": "SUPER_ADMIN",
        "name": "Super Administrador",
        "description": "Rol de referencia, no asignado en v1.0.",
        "is_system_role": True,
        "permissions": ["*:*:*"],
    },
]


def seed_roles() -> int:
    count = 0
    for data in _ROLES:
        role = db.session.query(Role).filter(Role.code == data["code"]).first()
        if role is None:
            db.session.add(Role(**data))
            count += 1
        else:
            role.name = data["name"]
            role.description = data["description"]
            role.is_system_role = data["is_system_role"]
            role.permissions = data["permissions"]
    db.session.commit()
    return count
