"""Workflow runs API — list and detail."""

from flask import g, jsonify, request

from . import api
from ..models import list_workflow_runs, get_workflow_run


@api.route("/workflows")
def get_workflows():
    project_id = request.args.get("project_id", type=int)
    workflow = request.args.get("workflow")
    status = request.args.get("status")
    return jsonify(list_workflow_runs(g.db, project_id, workflow, status))


@api.route("/workflows/<int:run_id>")
def get_workflow(run_id):
    result = get_workflow_run(g.db, run_id)
    if result is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)
