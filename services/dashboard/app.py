"""Flask application for the dev-team workflow dashboard."""

import os

from flask import Flask, g, jsonify, send_from_directory

from . import db
from .api import init_app

DEFAULT_PORT = 9876


def create_app():
    app = Flask(__name__, static_folder="static")

    @app.before_request
    def before_request():
        g.db = db.connect()

    @app.teardown_appcontext
    def close_db(exception):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    init_app(app)

    @app.route("/api/v1/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/")
    def overview():
        return send_from_directory(app.static_folder, "overview.html")

    @app.route("/workflow/<int:run_id>")
    def workflow_detail(run_id):
        return send_from_directory(app.static_folder, "detail.html")

    return app


def main():
    """Run the dashboard service."""
    port = int(os.environ.get("DEVTEAM_DASHBOARD_PORT", DEFAULT_PORT))
    app = create_app()
    print(f"Dev-Team Dashboard starting on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    main()
