#!/usr/bin/env python3
"""State resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    next_seq, slugify, now_iso, json_output,
)


def append(flags):
    session_id = require_flag(flags, "session")
    changed_by = require_flag(flags, "changed_by")
    state = require_flag(flags, "state")
    description = flags.get("description", "")

    d = require_session(session_id)
    state_dir = d / "state"
    seq = next_seq(state_dir)
    timestamp = now_iso()
    slug = slugify(changed_by)
    ts_slug = timestamp.replace(":", "-")
    file = state_dir / f"{seq}-{ts_slug}-{slug}.json"

    entry_id = f"{session_id}:state:{seq}"
    data = {
        "id": entry_id,
        "session_id": session_id,
        "creation_date": timestamp,
        "changed_by": changed_by,
        "state": state,
        "description": description,
    }
    file.write_text(json.dumps(data, ensure_ascii=False))
    print(file.read_text())


def current(flags):
    session_id = require_flag(flags, "session")
    changed_by = require_flag(flags, "changed_by")

    d = require_session(session_id)
    state_dir = d / "state"

    if not state_dir.is_dir():
        print(f"No state found for session: {session_id}", file=sys.stderr)
        sys.exit(1)

    slug = slugify(changed_by)
    matches = sorted(state_dir.glob(f"*-{slug}.json"))

    if not matches:
        print(f"No state found for changed_by: {changed_by}", file=sys.stderr)
        sys.exit(1)

    print(matches[-1].read_text())


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    state_dir = d / "state"

    if not state_dir.is_dir():
        print("[]")
        return

    results = []
    for f in sorted(state_dir.glob("*.json")):
        if f.is_file():
            results.append(json.loads(f.read_text()))

    json_output(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: state.py <append|current|list> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "append": append,
        "current": current,
        "list": list_all,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
