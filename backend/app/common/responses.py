"""Helpers for the uniform success response contract: {"data": ..., "meta": ...}."""
from __future__ import annotations

from typing import Any

from flask import jsonify


def success(data: Any = None, meta: dict | None = None, status: int = 200):
    return jsonify({"data": data, "meta": meta or {}}), status


def created(data: Any = None, meta: dict | None = None):
    return success(data, meta, status=201)


def accepted(data: Any = None, meta: dict | None = None):
    return success(data, meta, status=202)


def no_content():
    return "", 204
