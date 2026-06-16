"""Celery worker entrypoint.

Run with:  celery -A celery_worker.celery_app worker --beat --loglevel=info
"""
from app import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]

# Ensure task modules are imported so they register with the Celery app.
from app.tasks import generation, maintenance  # noqa: E402,F401
