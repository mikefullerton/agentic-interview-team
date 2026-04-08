#!/usr/bin/env python3
"""Team-result resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    now_iso, json_output,
)


def create(flags):
    session_id = require_flag(flags, "session")
    result_id = require_flag(flags, "result")
    specialist = require_flag(flags, "specialist")
    team = require_flag(flags, "team")

    d = require_session(session_id)
    teams_dir = d / "results" / specialist / "teams"
    teams_dir.mkdir(parents=True, exist_ok=True)

    team_result_id = f"{session_id}:team-result:{specialist}:{team}"
    team_file = teams_dir / f"{team}.json"

    ts = now_iso()
    data = {
        "team_result_id": team_result_id,
        "session_id": session_id,
        "result_id": result_id,
        "specialist": specialist,
        "team_name": team,
        "status": "running",
        "iteration": 0,
        "verifier_feedback": "",
        "consulting_annotations": [],
        "creation_date": ts,
        "modification_date": ts,
    }
    team_file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"team_result_id": team_result_id})


def get(flags):
    session_id = require_flag(flags, "session")
    specialist = require_flag(flags, "specialist")
    team = require_flag(flags, "team")

    d = require_session(session_id)
    team_file = d / "results" / specialist / "teams" / f"{team}.json"

    if not team_file.is_file():
        print(f"Team-result not found: {specialist}/{team}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(team_file.read_text())
    if "consulting_annotations" not in data:
        data["consulting_annotations"] = []
    print(json.dumps(data, ensure_ascii=False))


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    results_base = d / "results"

    if not results_base.is_dir():
        print("[]")
        return

    specialist_filter = flags.get("specialist", "")
    status_filter = flags.get("status", "")
    output = []
    for team_file in sorted(results_base.glob("*/teams/*.json")):
        if not team_file.is_file():
            continue
        data = json.loads(team_file.read_text())
        if "consulting_annotations" not in data:
            data["consulting_annotations"] = []
        if specialist_filter and data.get("specialist") != specialist_filter:
            continue
        if status_filter and data.get("status") != status_filter:
            continue
        output.append(data)

    json_output(output)


def update(flags):
    session_id = require_flag(flags, "session")
    specialist = require_flag(flags, "specialist")
    team = require_flag(flags, "team")

    d = require_session(session_id)
    team_file = d / "results" / specialist / "teams" / f"{team}.json"

    if not team_file.is_file():
        print(f"Team-result not found: {specialist}/{team}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(team_file.read_text())

    status = flags.get("status", "")
    if status:
        data["status"] = status

    iteration = flags.get("iteration", "")
    if iteration:
        data["iteration"] = int(iteration)

    verifier_feedback = flags.get("verifier_feedback", "")
    if verifier_feedback:
        data["verifier_feedback"] = verifier_feedback

    add_annotation = flags.get("add_consulting_annotation", "")
    if add_annotation:
        annotation = json.loads(add_annotation)
        if "consulting_annotations" not in data:
            data["consulting_annotations"] = []
        data["consulting_annotations"].append(annotation)

    data["modification_date"] = now_iso()
    team_file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"team_result_id": data["team_result_id"]})


def main():
    if len(sys.argv) < 2:
        print("Usage: team_result.py <create|get|list|update> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "get": get,
        "list": list_all,
        "update": update,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
