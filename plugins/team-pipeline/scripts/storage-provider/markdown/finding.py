#!/usr/bin/env python3
"""Finding resource for markdown arbitrator."""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    next_seq, slugify, now_iso, json_output,
)


def _parse_finding_id(finding_id: str):
    """Parse composite ID: <session-id>:finding:<specialist>:<seq>"""
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
    result_id = require_flag(flags, "result")
    specialist = require_flag(flags, "specialist")
    category = require_flag(flags, "category")
    severity = require_flag(flags, "severity")
    title = require_flag(flags, "title")
    detail = require_flag(flags, "detail")

    d = require_session(session_id)
    findings_dir = d / "results" / specialist / "findings"
    seq = next_seq(findings_dir)
    slug = slugify(title)
    file = findings_dir / f"{seq}-{slug}.json"

    finding_id = f"{session_id}:finding:{specialist}:{seq}"
    data = {
        "finding_id": finding_id,
        "result_id": result_id,
        "session_id": session_id,
        "specialist": specialist,
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "creation_date": now_iso(),
        "linked_artifacts": [],
    }
    file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"finding_id": finding_id})


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    results_base = d / "results"

    if not results_base.is_dir():
        print("[]")
        return

    specialist_filter = flags.get("specialist", "")
    severity_filter = flags.get("severity", "")
    output = []
    for finding_file in sorted(results_base.glob("*/findings/*.json")):
        if not finding_file.is_file():
            continue
        data = json.loads(finding_file.read_text())
        if specialist_filter and data.get("specialist") != specialist_filter:
            continue
        if severity_filter and data.get("severity") != severity_filter:
            continue
        output.append(data)

    json_output(output)


def get(flags):
    finding_id = require_flag(flags, "finding")

    session_id, specialist, seq = _parse_finding_id(finding_id)
    if not session_id:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)

    d = require_session(session_id)
    findings_dir = d / "results" / specialist / "findings"

    matches = sorted(findings_dir.glob(f"{seq}-*.json"))
    if not matches or not matches[0].is_file():
        print(f"Finding not found: {finding_id}", file=sys.stderr)
        sys.exit(1)

    print(matches[0].read_text())


def link_artifact(flags):
    finding_id = require_flag(flags, "finding")
    artifact_id = require_flag(flags, "artifact")

    session_id, specialist, seq = _parse_finding_id(finding_id)
    if not session_id:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)

    d = require_session(session_id)
    findings_dir = d / "results" / specialist / "findings"

    matches = sorted(findings_dir.glob(f"{seq}-*.json"))
    if not matches or not matches[0].is_file():
        print(f"Finding not found: {finding_id}", file=sys.stderr)
        sys.exit(1)

    finding_file = matches[0]
    data = json.loads(finding_file.read_text())
    data["linked_artifacts"].append(artifact_id)
    finding_file.write_text(json.dumps(data, ensure_ascii=False))

    json_output({"finding_id": finding_id, "artifact_id": artifact_id})


def main():
    if len(sys.argv) < 2:
        print("Usage: finding.py <create|list|get|link-artifact> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "list": list_all,
        "get": get,
        "link-artifact": link_artifact,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
