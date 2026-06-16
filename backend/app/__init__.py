"""Application factory for the VirtualRadio API."""
from __future__ import annotations

import click
from flask import Flask

from app.config import get_config
from app.extensions import celery_init_app, db, jwt, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # --- Logging ---
    from app.common.logging import configure_logging

    configure_logging(app)

    # --- CORS ---
    from flask_cors import CORS

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    celery_init_app(app)

    # --- Models (populate metadata) + JWT callbacks ---
    from app import models  # noqa: F401
    from app.auth.jwt_callbacks import register_jwt_callbacks

    register_jwt_callbacks(jwt)

    # --- Error handlers + routes ---
    from app.common.errors import register_error_handlers
    from app.routes import register_blueprints

    register_error_handlers(app)
    register_blueprints(app)

    _register_cli(app)
    return app


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed-roles")
    def seed_roles_command():
        """Seed the RBAC role catalog (idempotent)."""
        from app.seeds.roles import seed_roles

        count = seed_roles()
        click.echo(f"Roles seeded/verified: {count}")

    @app.cli.command("seed-demo")
    @click.argument("email")
    @click.option("--password", default="password123", show_default=True)
    def seed_demo_command(email, password):
        """Create a demo user with a fully seeded universe."""
        from app.models import User
        from app.seeds.universe import seed_default_universe

        existing = db.session.query(User).filter(User.email == email.lower()).first()
        if existing:
            click.echo(f"User {email} already exists ({existing.id})")
            return
        user = User(email=email.lower(), display_name="Demo")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        seed_default_universe(user.id)
        db.session.commit()
        click.echo(f"Demo user created: {email} / {password}  (id={user.id})")
