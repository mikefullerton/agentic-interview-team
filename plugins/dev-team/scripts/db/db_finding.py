#!/usr/bin/env python3
"""db-finding — Record or update a finding.
Usage: db_finding.py --session-state <id> --project <id> --type <type> --severity <sev> --description "<text>" [--artifact-path <path>]
       db_finding.py update --id <id> --status <accepted|rejected|fixed>
       db_finding.py --list --project <id> [--type <type>] [--status <status>]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output, row_to_dict


def main():
    init_db()
    argv = sys.argv[1:]

    action = "create"
    if argv and argv[0] == "update":
        action = "update"
        argv = argv[1:]
    elif "--list" in argv:
        action = "list"
        argv = [a for a in argv if a != "--list"]

    flags = parse_flags(argv)

    conn = connect()
    try:
        if action == "create":
            project_id = int(require_flag(flags, "project"))
            finding_type = require_flag(flags, "type")
            description = require_flag(flags, "description")
            session_state_id = flags.get("session_state") or None
            if session_state_id is not None:
                session_state_id = int(session_state_id)
            severity = flags.get("severity") or None
            artifact_path = flags.get("artifact_path") or None
            cur = conn.execute(
                "INSERT INTO findings (session_state_id, project_id, type, severity, description, artifact_path) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_state_id, project_id, finding_type, severity, description, artifact_path)
            )
            conn.commit()
            json_output({"id": cur.lastrowid})

        elif action == "update":
            finding_id = int(require_flag(flags, "id"))
            status = require_flag(flags, "status")
            conn.execute(
                "UPDATE findings SET status=? WHERE id=?",
                (status, finding_id)
            )
            conn.commit()
            json_output({"id": finding_id, "status": status})

        elif action == "list":
            project_id = int(require_flag(flags, "project"))
            sql = "SELECT * FROM findings WHERE project_id=?"
            params: list = [project_id]
            if flags.get("type"):
                sql += " AND type=?"
                params.append(flags["type"])
            if flags.get("status"):
                sql += " AND status=?"
                params.append(flags["status"])
            sql += " ORDER BY created DESC"
            cur = conn.execute(sql, params)
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        else:
            print("Usage: db_finding.py [create|update|--list] [options]", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
