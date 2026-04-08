#!/usr/bin/env python3
"""Result resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    now_iso, json_output,
)


def create(flags):
    session_id = require_flag(flags, "session")
    specialist = require_flag(flags, "specialist")

    d = require_session(session_id)
    result_dir = d / "results" / specialist
    result_dir.mkdir(parents=True, exist_ok=True)

    result_id = f"{session_id}:result:{specialist}"
    data = {
        "result_id": result_id,
        "session_id": session_id,
        "specialist": specialist,
        "creation_date": now_iso(),
    }
    (result_dir / "result.json").write_text(json.dumps(data, ensure_ascii=False))

    json_output({"result_id": result_id})


def get(flags):
    result_id = require_flag(flags, "result")

    # Parse composite ID: <session-id>:result:<specialist>
    parts = result_id.split(":result:", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        print(f"Invalid result ID format: {result_id}", file=sys.stderr)
        sys.exit(1)

    session_id, specialist = parts[0], parts[1]
    d = require_session(session_id)
    result_file = d / "results" / specialist / "result.json"

    if not result_file.is_file():
        print(f"Result not found: {result_id}", file=sys.stderr)
        sys.exit(1)

    print(result_file.read_text())


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    results_base = d / "results"

    if not results_base.is_dir():
        print("[]")
        return

    specialist_filter = flags.get("specialist", "")
    output = []
    for result_file in sorted(results_base.glob("*/result.json")):
        if not result_file.is_file():
            continue
        data = json.loads(result_file.read_text())
        if specialist_filter and data.get("specialist") != specialist_filter:
            continue
        output.append(data)

    json_output(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: result.py <create|get|list> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "get": get,
        "list": list_all,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
