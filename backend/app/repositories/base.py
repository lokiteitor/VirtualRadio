"""Base repository enforcing owner-scoped data access (RBAC scope ``own``).

Every query is filtered by ``owner_id = current_user.id`` and ``owner_id`` is
taken from the JWT identity on create — never from the request body. Accessing a
resource owned by another user raises 404 (not 403) so its existence is hidden.
"""
from __future__ import annotations

import uuid
from typing import Any

from flask_jwt_extended import current_user
from sqlalchemy.exc import IntegrityError

from app.common.errors import ConflictError, NotFoundError
from app.extensions import db


def current_owner_id() -> uuid.UUID:
    return current_user.id


def scoped_query(model):
    """Return a query for *model* filtered to the current user's rows."""
    return db.session.query(model).filter(model.owner_id == current_user.id)


def coerce_uuid(value: Any) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


class BaseRepository:
    model = None  # set by subclasses

    # --- Read ---
    def query(self):
        return scoped_query(self.model)

    def list(self, *, order_by=None, **filters):
        query = self.query()
        for field, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, field) == value)
        if order_by is not None:
            query = query.order_by(order_by)
        return query.all()

    def get_or_none(self, obj_id):
        uid = coerce_uuid(obj_id)
        if uid is None:
            return None
        return self.query().filter(self.model.id == uid).first()

    def get(self, obj_id):
        obj = self.get_or_none(obj_id)
        if obj is None:
            raise NotFoundError()
        return obj

    # --- Write ---
    def create(self, **data):
        obj = self.model(owner_id=current_user.id, **data)
        db.session.add(obj)
        self._commit()
        return obj

    def update(self, obj, **data):
        for field, value in data.items():
            setattr(obj, field, value)
        self._commit()
        return obj

    def delete(self, obj) -> None:
        db.session.delete(obj)
        self._commit()

    # --- Internal ---
    def _commit(self) -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise ConflictError("El recurso ya existe o viola una restricción") from exc
