#!/usr/bin/env python3
"""Reference resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    next_seq, slugify, now_iso, json_output,
)


def create(flags):
    result_id = require_flag(flags, "result")
    path = require_flag(flags, "path")
    type_ = require_flag(flags, "type")

    # Parse session ID and specialist from composite result ID: <session-id>:result:<specialist>
    parts = result_id.split(":result:", 1)
    session_id = parts[0]
    specialist = parts[1] if len(parts) == 2 else ""

    d = require_session(session_id)
    ref_dir = d / "results" / specialist / "references"
    seq = next_seq(ref_dir)
    path_slug = slugify(path)
    file = ref_dir / f"{seq}-{type_}-{path_slug}.json"

    reference_id = f"{result_id}:reference:{seq}"
    data = {
        "reference_id": reference_id,
        "result_id": result_id,
        "path": path,
        "type": type_,
        "creation_date": now_iso(),
    }
    file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"reference_id": reference_id})


def list_all(flags):
    result_id = require_flag(flags, "result")

    # Parse session ID and specialist from composite result ID: <session-id>:result:<specialist>
    parts = result_id.split(":result:", 1)
    session_id = parts[0]
    specialist = parts[1] if len(parts) == 2 else ""

    d = require_session(session_id)
    ref_dir = d / "results" / specialist / "references"

    if not ref_dir.is_dir():
        print("[]")
        return

    results = []
    for f in sorted(ref_dir.glob("*.json")):
        if f.is_file():
            results.append(json.loads(f.read_text()))

    json_output(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: reference.py <create|list> [flags]", file=sys.stderr)
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
