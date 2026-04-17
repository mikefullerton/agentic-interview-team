#!/usr/bin/env python3
"""Report resource for markdown arbitrator.

Reports are NOT stored — they compose from existing data.
Actions: overview, specialist, finding, trace
"""
import json
import sys
from storage_helpers import (
    parse_flags, require_flag, require_session,
    session_dir, json_output,
)


def overview(flags):
    session_id = require_flag(flags, "session")
    d = require_session(session_id)

    # Session metadata
    session = json.loads((d / "session.json").read_text())

    # Current state (latest state transition)
    current_state = None
    state_dir = d / "state"
    if state_dir.is_dir():
        state_files = sorted(state_dir.glob("*.json"))
        if state_files:
            current_state = json.loads(state_files[-1].read_text())

    # Specialist summary
    specialists = []
    results_dir = d / "results"
    if results_dir.is_dir():
        for spec_dir in sorted(results_dir.iterdir()):
            if not spec_dir.is_dir():
                continue
            spec = spec_dir.name
            findings_count = 0
            findings_dir = spec_dir / "findings"
            if findings_dir.is_dir():
                findings_count = sum(1 for f in findings_dir.glob("*.json") if f.is_file())
            specialists.append({"specialist": spec, "findings_count": findings_count})

    json_output({
        "session": session,
        "current_state": current_state,
        "specialists": specialists,
    })


def specialist(flags):
    session_id = require_flag(flags, "session")
    specialist_name = require_flag(flags, "specialist")
    d = require_session(session_id)

    spec_dir = d / "results" / specialist_name
    if not spec_dir.is_dir():
        print(json.dumps({"error": f"No results for specialist: {specialist_name}"}), file=sys.stderr)
        sys.exit(1)

    # Result metadata
    result = json.loads((spec_dir / "result.json").read_text())

    # All findings
    findings = []
    findings_dir = spec_dir / "findings"
    if findings_dir.is_dir():
        for f in sorted(findings_dir.glob("*.json")):
            if f.is_file():
                findings.append(json.loads(f.read_text()))

    # All interpretations
    interpretations = []
    interp_dir = spec_dir / "interpretations"
    if interp_dir.is_dir():
        for f in sorted(interp_dir.glob("*.json")):
            if f.is_file():
                interpretations.append(json.loads(f.read_text()))

    # All references
    references = []
    ref_dir = spec_dir / "references"
    if ref_dir.is_dir():
        for f in sorted(ref_dir.glob("*.json")):
            if f.is_file():
                references.append(json.loads(f.read_text()))

    json_output({
        "result": result,
        "findings": findings,
        "interpretations": interpretations,
        "references": references,
    })


def finding(flags):
    finding_id = require_flag(flags, "finding")

    # Parse composite ID: <session-id>:finding:<specialist>:<seq>
    parts = finding_id.split(":finding:", 1)
    if len(parts) != 2 or not parts[0] or parts[0] == finding_id:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)
    session_id = parts[0]
    remainder = parts[1]
    sub = remainder.split(":", 1)
    if len(sub) != 2:
        print(f"Invalid finding ID format: {finding_id}", file=sys.stderr)
        sys.exit(1)
    specialist_name, seq = sub[0], sub[1]

    d = require_session(session_id)
    findings_dir = d / "results" / specialist_name / "findings"

    matches = sorted(findings_dir.glob(f"{seq}-*.json"))
    if not matches or not matches[0].is_file():
        print(f"Finding not found: {finding_id}", file=sys.stderr)
        sys.exit(1)

    finding_data = json.loads(matches[0].read_text())

    # Find matching interpretation
    interp_dir = d / "results" / specialist_name / "interpretations"
    interpretation = None
    interp_file = interp_dir / f"{seq}-interpretation.json"
    if interp_file.is_file():
        interpretation = json.loads(interp_file.read_text())

    # Linked artifacts
    linked_artifacts = []
    artifact_ids = finding_data.get("linked_artifacts", [])
    if artifact_ids:
        artifacts_dir = d / "artifacts"
        for aid in artifact_ids:
            aid_seq = aid.split(":")[-1]
            af_matches = sorted(artifacts_dir.glob(f"{aid_seq}-*.json"))
            if af_matches and af_matches[0].is_file():
                linked_artifacts.append(json.loads(af_matches[0].read_text()))

    json_output({
        "finding": finding_data,
        "interpretation": interpretation,
        "linked_artifacts": linked_artifacts,
    })


def trace(flags):
    session_id = require_flag(flags, "session")
    d = require_session(session_id)

    # All state transitions in order
    states = []
    state_dir = d / "state"
    if state_dir.is_dir():
        for f in sorted(state_dir.glob("*.json")):
            if f.is_file():
                states.append(json.loads(f.read_text()))

    # All retries in order
    retries = []
    retry_dir = d / "retries"
    if retry_dir.is_dir():
        for f in sorted(retry_dir.glob("*.json")):
            if f.is_file():
                retries.append(json.loads(f.read_text()))

    # All messages in order
    messages = []
    msg_dir = d / "messages"
    if msg_dir.is_dir():
        for f in sorted(msg_dir.glob("*.json")):
            if f.is_file():
                messages.append(json.loads(f.read_text()))

    json_output({
        "states": states,
        "retries": retries,
        "messages": messages,
    })


def main():
    if len(sys.argv) < 2:
        print("Usage: report.py <overview|specialist|finding|trace> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "overview": overview,
        "specialist": specialist,
        "finding": finding,
        "trace": trace,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
