"""API blueprint registration."""

from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api/v1")


def init_app(app):
    """Register all API route modules."""
    from . import workflows, messages, projects
    app.register_blueprint(api)
