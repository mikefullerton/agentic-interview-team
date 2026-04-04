#!/usr/bin/env python3
"""Session resource for markdown arbitrator."""
import json
import sys
from pathlib import Path
from _lib import (
    parse_flags, require_flag, require_session,
    new_session_id, session_dir, now_iso, json_output, SESSION_BASE,
)


def create(flags):
    playbook = require_flag(flags, "playbook")
    team_lead = require_flag(flags, "team_lead")
    user = require_flag(flags, "user")
    machine = require_flag(flags, "machine")

    session_id = new_session_id()
    d = session_dir(session_id)
    d.mkdir(parents=True, exist_ok=True)

    data = {
        "session_id": session_id,
        "playbook": playbook,
        "team_lead": team_lead,
        "user": user,
        "machine": machine,
        "creation_date": now_iso(),
    }
    (d / "session.json").write_text(json.dumps(data, ensure_ascii=False))

    json_output({"session_id": session_id})


def get(flags):
    session_id = require_flag(flags, "session")
    d = require_session(session_id)
    print((d / "session.json").read_text())


def list_all(flags):
    if not SESSION_BASE.is_dir():
        print("[]")
        return

    results = []
    for session_file in sorted(SESSION_BASE.glob("*/session.json")):
        if not session_file.is_file():
            continue
        data = json.loads(session_file.read_text())
        match = True

        playbook_filter = flags.get("playbook", "")
        if playbook_filter and data.get("playbook") != playbook_filter:
            match = False

        status_filter = flags.get("status", "")
        if status_filter and match:
            sid = data.get("session_id", "")
            state_dir = session_dir(sid) / "state"
            if state_dir.is_dir():
                state_files = sorted(state_dir.glob("*.json"))
                if state_files:
                    latest = json.loads(state_files[-1].read_text())
                    if latest.get("state") != status_filter:
                        match = False
                else:
                    match = False
            else:
                match = False

        if match:
            results.append(data)

    json_output(results)


def add_path(flags):
    session_id = require_flag(flags, "session")
    path = require_flag(flags, "path")
    type_ = require_flag(flags, "type")

    d = require_session(session_id)
    paths_file = d / "paths.jsonl"

    entry = {
        "session_id": session_id,
        "path": path,
        "type": type_,
        "creation_date": now_iso(),
    }
    with paths_file.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    json_output({"session_id": session_id, "path": path, "type": type_})


def main():
    if len(sys.argv) < 2:
        print("Usage: session.py <create|get|list|add-path> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "get": get,
        "list": list_all,
        "add-path": add_path,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
