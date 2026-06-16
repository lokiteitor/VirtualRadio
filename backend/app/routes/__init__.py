"""Blueprint auto-registration.

Every module in this package that exposes a ``bp`` Blueprint is registered
automatically under the API prefix (``/api/v1``). New resources only need to
drop a ``routes/<resource>.py`` file with a ``bp`` — no shared file edits.
"""
from __future__ import annotations

import importlib
import pkgutil

from flask import Blueprint, Flask


def register_blueprints(app: Flask) -> None:
    import app.routes as routes_pkg

    prefix = app.config.get("API_PREFIX", "/api/v1")
    for _finder, module_name, _is_pkg in pkgutil.iter_modules(routes_pkg.__path__):
        module = importlib.import_module(f"app.routes.{module_name}")
        bp = getattr(module, "bp", None)
        if isinstance(bp, Blueprint):
            app.register_blueprint(bp, url_prefix=prefix)
