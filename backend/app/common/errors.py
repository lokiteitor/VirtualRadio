"""Application error types and global error handlers.

Error contract:  {"error": {"code", "message", "details"}}
"""
from __future__ import annotations

from typing import Any

from flask import Flask, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Base class for all application errors mapped to the error envelope."""

    code = "INTERNAL_ERROR"
    message = "Ha ocurrido un error inesperado"
    status = 500

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status: int | None = None,
        details: dict | None = None,
    ):
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        self.details: dict[str, Any] = details or {}


class NotFoundError(ApiError):
    code = "NOT_FOUND"
    message = "Recurso no encontrado"
    status = 404


class UnauthorizedError(ApiError):
    code = "UNAUTHORIZED"
    message = "Token inválido o ausente"
    status = 401


class ForbiddenError(ApiError):
    code = "FORBIDDEN"
    message = "No tienes permiso para esta operación"
    status = 403


class ValidationFailedError(ApiError):
    code = "VALIDATION_ERROR"
    message = "Los datos enviados no son válidos"
    status = 422


class ConflictError(ApiError):
    code = "CONFLICT"
    message = "El recurso ya existe"
    status = 409


def _error_payload(code: str, message: str, details: dict | None = None):
    return jsonify({"error": {"code": code, "message": message, "details": details or {}}})


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):
        return _error_payload(err.code, err.message, err.details), err.status

    @app.errorhandler(MarshmallowValidationError)
    def _handle_validation(err: MarshmallowValidationError):
        return (
            _error_payload(
                "VALIDATION_ERROR",
                "Los datos enviados no son válidos",
                err.messages if isinstance(err.messages, dict) else {"_": err.messages},
            ),
            422,
        )

    @app.errorhandler(HTTPException)
    def _handle_http(err: HTTPException):
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }
        code = code_map.get(err.code, "HTTP_ERROR")
        return _error_payload(code, err.description or err.name), err.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected(err: Exception):
        app.logger.exception("Unhandled exception: %s", err)
        return _error_payload("INTERNAL_ERROR", "Ha ocurrido un error inesperado"), 500
