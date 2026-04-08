#!/usr/bin/env python3
"""Artifact resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    next_seq, slugify, now_iso, json_output,
)


def create(flags):
    session_id = require_flag(flags, "session")
    artifact = require_flag(flags, "artifact")
    message = flags.get("message", "")
    description = flags.get("description", "")

    d = require_session(session_id)
    artifact_dir = d / "artifacts"
    seq = next_seq(artifact_dir)
    slug = slugify(artifact)
    file = artifact_dir / f"{seq}-{slug}.json"

    artifact_id = f"{session_id}:artifact:{seq}"
    data = {
        "artifact_id": artifact_id,
        "session_id": session_id,
        "artifact": artifact,
        "message": message,
        "description": description,
        "creation_date": now_iso(),
        "linked_states": [],
    }
    file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"artifact_id": artifact_id})


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    artifact_dir = d / "artifacts"

    if not artifact_dir.is_dir():
        print("[]")
        return

    results = []
    for f in sorted(artifact_dir.glob("*.json")):
        if f.is_file():
            results.append(json.loads(f.read_text()))

    json_output(results)


def link_state(flags):
    artifact_id = require_flag(flags, "artifact")
    state_id = require_flag(flags, "state")

    # Parse session ID from composite artifact ID: <session-id>:artifact:NNNN
    parts = artifact_id.split(":artifact:", 1)
    session_id = parts[0]
    seq = parts[1] if len(parts) == 2 else ""

    d = require_session(session_id)
    artifact_dir = d / "artifacts"

    matches = sorted(artifact_dir.glob(f"{seq}-*.json"))
    if not matches:
        print(f"Artifact not found: {artifact_id}", file=sys.stderr)
        sys.exit(1)

    artifact_file = matches[0]
    data = json.loads(artifact_file.read_text())
    data["linked_states"].append(state_id)
    artifact_file.write_text(json.dumps(data, ensure_ascii=False))
    print(artifact_file.read_text())


def main():
    if len(sys.argv) < 2:
        print("Usage: artifact.py <create|list|link-state> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "list": list_all,
        "link-state": link_state,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
