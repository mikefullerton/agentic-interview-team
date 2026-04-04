#!/usr/bin/env python3
"""Interpretation resource for markdown arbitrator."""
import json
import sys
from _lib import (
    parse_flags, require_flag, require_session,
    session_dir, now_iso, json_output,
)


def _parse_finding_id(finding_id: str):
    """Parse composite finding ID: <session-id>:finding:<specialist>:<seq>"""
    parts = finding_id.split(":finding:", 1)
    if len(parts) != 2 or not parts[0] or parts[0] == finding_id:
        return None, None, None
    session_id = parts[0]
    remainder = parts[1]
    sub = remainder.split(":", 1)
    if len(sub) != 2 or not sub[0] or not sub[1]:
        return None, None, None
    return session_id, sub[0], sub[1]


def create(flags):
    session_id = require_flag(flags, "session")
    finding_id = require_flag(flags, "finding")
    specialist = require_flag(flags, "specialist")
    interpretation = require_flag(flags, "interpretation")

    d = require_session(session_id)

    # Parse composite finding ID to extract seq
    finding_remainder = finding_id.split(":finding:", 1)
    if len(finding_remainder) < 2:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)
    finding_seq = finding_remainder[1].split(":")[-1]
    if not finding_seq or finding_remainder[1] == finding_id:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)

    interp_dir = d / "results" / specialist / "interpretations"
    interp_dir.mkdir(parents=True, exist_ok=True)

    interp_file = interp_dir / f"{finding_seq}-interpretation.json"
    interpretation_id = f"{session_id}:interpretation:{specialist}:{finding_seq}"

    data = {
        "interpretation_id": interpretation_id,
        "finding_id": finding_id,
        "session_id": session_id,
        "specialist": specialist,
        "interpretation": interpretation,
        "creation_date": now_iso(),
    }
    interp_file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"interpretation_id": interpretation_id})


def list_all(flags):
    finding_id = require_flag(flags, "finding")

    session_id, specialist, finding_seq = _parse_finding_id(finding_id)
    if not session_id:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)

    d = session_dir(session_id)
    interp_dir = d / "results" / specialist / "interpretations"

    if not interp_dir.is_dir():
        print("[]")
        return

    output = []
    interp_file = interp_dir / f"{finding_seq}-interpretation.json"
    if interp_file.is_file():
        output.append(json.loads(interp_file.read_text()))

    json_output(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: interpretation.py <create|list> [flags]", file=sys.stderr)
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
