"""Sessions API — list and detail."""

from flask import g, jsonify, request

from . import api
from ..models import list_sessions, get_session


@api.route("/workflows")
def get_workflows():
    project_id = request.args.get("project_id", type=int)
    workflow = request.args.get("workflow")
    status = request.args.get("status")
    return jsonify(list_sessions(g.db, project_id, workflow, status))


@api.route("/workflows/<int:run_id>")
def get_workflow(run_id):
    result = get_session(g.db, run_id)
    if result is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)
