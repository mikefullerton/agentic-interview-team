#!/usr/bin/env python3
# resume_session.py — Detect interrupted sessions for a given playbook
# Usage: resume_session.py --playbook <name>
#
# Output: JSON with interrupted session info or {"interrupted": false}

import sys
import json
import os
import subprocess
import argparse
from pathlib import Path


def run_arbitrator(arbitrator_path, *args):
    """Run arbitrator.sh with given args, return parsed JSON or default."""
    try:
        result = subprocess.run(
            [arbitrator_path] + list(args),
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return []


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--playbook", default="")
    args, _ = parser.parse_known_args()

    if not args.playbook:
        print("Usage: resume_session.py --playbook <name>", file=sys.stderr)
        sys.exit(1)

    script_dir = Path(__file__).parent
    arbitrator = str(script_dir / "arbitrator.sh")
    playbook = args.playbook

    session_base = os.environ.get(
        "ARBITRATOR_SESSION_BASE",
        str(Path.home() / ".agentic-cookbook" / "dev-team" / "sessions"),
    )

    # Find sessions for this playbook
    all_sessions = run_arbitrator(arbitrator, "session", "list", "--playbook", playbook)

    interrupted_sessions = []
    for session in all_sessions:
        session_id = session.get("session_id", "")
        session_dir = Path(session_base) / session_id / "state"

        if session_dir.is_dir():
            state_files = sorted(session_dir.glob("*.json"))
            if state_files:
                latest_state_file = state_files[-1]
                try:
                    with open(latest_state_file) as f:
                        state_data = json.load(f)
                    latest_state = state_data.get("state", "")
                    if latest_state not in ("completed", "abandoned"):
                        interrupted_sessions.append(session)
                except (json.JSONDecodeError, OSError):
                    pass

    if not interrupted_sessions:
        print(json.dumps({"interrupted": False}))
        sys.exit(0)

    # Use the most recent interrupted session
    session = interrupted_sessions[-1]
    session_id = session.get("session_id", "")
    creation_date = session.get("creation_date", "")

    # Build specialist progress summary
    results = run_arbitrator(arbitrator, "result", "list", "--session", session_id)
    specialists = []

    for row in results:
        specialist = row.get("specialist", "")
        team_results = run_arbitrator(
            arbitrator, "team-result", "list", "--session", session_id, "--specialist", specialist
        )
        total = len(team_results)
        completed = sum(
            1 for r in team_results if r.get("status") in ("passed", "escalated")
        )
        escalated = sum(1 for r in team_results if r.get("status") == "escalated")
        specialists.append(
            {
                "name": specialist,
                "teams_completed": completed,
                "teams_total": total,
                "teams_escalated": escalated,
            }
        )

    output = {
        "interrupted": True,
        "session_id": session_id,
        "creation_date": creation_date,
        "specialists": specialists,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
