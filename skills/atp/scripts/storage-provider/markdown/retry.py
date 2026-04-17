#!/usr/bin/env python3
"""Retry resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    next_seq, now_iso, json_output,
)


def create(flags):
    session_id = require_flag(flags, "session")
    state_id = require_flag(flags, "state")
    reason = require_flag(flags, "reason")

    d = require_session(session_id)
    retry_dir = d / "retries"
    seq = next_seq(retry_dir)
    timestamp = now_iso()
    ts_slug = timestamp.replace(":", "-")
    file = retry_dir / f"{seq}-{ts_slug}.json"

    retry_id = f"{session_id}:retry:{seq}"
    data = {
        "retry_id": retry_id,
        "session_id": session_id,
        "session_state_id": state_id,
        "reason": reason,
        "creation_date": timestamp,
    }
    file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"retry_id": retry_id})


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    retry_dir = d / "retries"

    if not retry_dir.is_dir():
        print("[]")
        return

    results = []
    for f in sorted(retry_dir.glob("*.json")):
        if f.is_file():
            results.append(json.loads(f.read_text()))

    json_output(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: retry.py <create|list> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "list": list_all,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
