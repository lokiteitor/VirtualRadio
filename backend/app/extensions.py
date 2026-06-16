"""Shared Flask extensions and the SQLAlchemy declarative base.

Exposes the singletons (db, migrate, jwt) used across the app and the Celery
factory that binds tasks to the Flask application context.
"""
from __future__ import annotations

from celery import Celery, Task
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single declarative base for all models."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
jwt = JWTManager()


def celery_init_app(app: Flask) -> Celery:
    """Create a Celery app whose tasks run inside the Flask app context."""

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
