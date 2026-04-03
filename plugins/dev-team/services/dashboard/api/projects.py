"""Projects API — list all projects."""

from flask import g, jsonify

from . import api
from ..models import list_projects


@api.route("/projects")
def get_projects():
    return jsonify(list_projects(g.db))
