"""Messages API — incremental fetch for live transcript."""

from flask import g, jsonify, request

from . import api
from ..models import list_messages


@api.route("/workflows/<int:run_id>/messages")
def get_messages(run_id):
    since = request.args.get("since", 0, type=int)
    return jsonify(list_messages(g.db, run_id, since))
