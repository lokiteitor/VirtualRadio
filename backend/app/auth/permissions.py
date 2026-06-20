"""RBAC permission catalog and the check_permission decorator.

Deliberately simple model: a single system role ``USER`` with a single effective
scope ``own``. Every protected endpoint declares its required permission as
``resource:action:scope``; ownership is enforced downstream by ``scoped_query``.
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import current_user, verify_jwt_in_request

from app.common.errors import ForbiddenError, UnauthorizedError

# Permissions granted to the single system role USER (see docs/backend/rbac.md).
USER_PERMISSIONS: frozenset[str] = frozenset(
    {
        # Stations
        "station:create:own", "station:read:own", "station:update:own",
        "station:delete:own", "station:suggest:own",
        "station:read_settings:own", "station:update_settings:own",
        "station:read_music:own", "station:update_music:own",
        # Episodes & jobs
        "episode:read:own", "episode:generate:own", "episode:delete:own",
        "job:read:own",
        # Universe
        "universe:read:own",
        # Music
        "music:read:own", "music:upload:own", "music:scan:own", "music:delete:own",
        # News
        "news:create:own", "news:read:own", "news:update:own",
        "news:delete:own", "news:suggest:own",
        # Brands
        "brand:create:own", "brand:read:own", "brand:update:own",
        "brand:delete:own", "brand:suggest:own",
        # Commercials
        "commercial:create:own", "commercial:read:own", "commercial:update:own",
        "commercial:delete:own", "commercial:suggest:own",
        # Characters
        "character:create:own", "character:read:own", "character:update:own",
        "character:delete:own", "character:suggest:own", "character:read_memories:own",
        # Story events
        "story_event:create:own", "story_event:read:own",
        "story_event:update:own", "story_event:delete:own",
    }
)

# Reference-only super role (not assigned to any user in v1.0).
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "USER": USER_PERMISSIONS,
    "SUPER_ADMIN": frozenset({"*:*:*"}),
}


def has_permission(permissions: frozenset[str], resource: str, action: str, scope: str) -> bool:
    if "*:*:*" in permissions:
        return True
    return f"{resource}:{action}:{scope}" in permissions


def check_permission(resource: str, action: str, scope: str = "own"):
    """Verify a valid JWT, an active user, and that the role grants the permission."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user
            if user is None or not getattr(user, "is_active", False):
                raise UnauthorizedError("Token inválido o usuario inactivo")
            if not has_permission(user.permissions, resource, action, scope):
                raise ForbiddenError(f"Falta el permiso {resource}:{action}:{scope}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
