#!/usr/bin/env python3
"""db-run — Start or complete a session.
Usage: db_run.py start --project <id> --workflow <name>
       db_run.py complete --id <id> --status <completed|failed|interrupted>
       db_run.py --get <id>
       db_run.py --latest --project <id> --workflow <name>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output, row_to_dict


def main():
    init_db()
    argv = sys.argv[1:]

    # Determine action
    action = ""
    if argv and argv[0] in ("start", "complete"):
        action = argv[0]
        argv = argv[1:]
    elif "--get" in argv:
        idx = argv.index("--get")
        action = "get"
        # pull the value out so parse_flags can pick it up via --id
        # but --get takes the next arg as the id
        session_id = argv[idx + 1] if idx + 1 < len(argv) else ""
        argv = ["--id", session_id] + argv[:idx] + argv[idx + 2:]
    elif "--latest" in argv:
        action = "latest"
        argv = [a for a in argv if a != "--latest"]

    flags = parse_flags(argv)

    conn = connect()
    try:
        if action == "start":
            project_id = int(require_flag(flags, "project"))
            workflow = require_flag(flags, "workflow")
            cur = conn.execute(
                "INSERT INTO sessions (project_id, workflow) VALUES (?, ?)",
                (project_id, workflow)
            )
            conn.commit()
            json_output({"id": cur.lastrowid})

        elif action == "complete":
            session_id = int(require_flag(flags, "id"))
            status = require_flag(flags, "status")
            conn.execute(
                "UPDATE sessions SET status=?, completed=CURRENT_TIMESTAMP WHERE id=?",
                (status, session_id)
            )
            conn.commit()
            json_output({"id": session_id, "status": status})

        elif action == "get":
            session_id = int(require_flag(flags, "id"))
            cur = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        elif action == "latest":
            project_id = int(require_flag(flags, "project"))
            workflow = require_flag(flags, "workflow")
            cur = conn.execute(
                "SELECT * FROM sessions WHERE project_id=? AND workflow=? ORDER BY started DESC LIMIT 1",
                (project_id, workflow)
            )
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        else:
            print("Usage: db_run.py start|complete|--get|--latest [options]", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
