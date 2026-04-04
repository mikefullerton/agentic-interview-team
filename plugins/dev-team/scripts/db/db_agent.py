#!/usr/bin/env python3
"""db-agent — Start or complete a state transition.
Usage: db_agent.py start --run <id> --agent <type> [--specialist <domain>]
       db_agent.py complete --id <id> --status <completed|failed> [--output-path <path>]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output


def main():
    init_db()
    argv = sys.argv[1:]

    action = ""
    if argv and argv[0] in ("start", "complete"):
        action = argv[0]
        argv = argv[1:]

    flags = parse_flags(argv)

    conn = connect()
    try:
        if action == "start":
            session_id = int(require_flag(flags, "run"))
            agent_type = require_flag(flags, "agent")
            specialist = flags.get("specialist") or None
            cur = conn.execute(
                "INSERT INTO session_state (session_id, agent_type, specialist_domain) VALUES (?, ?, ?)",
                (session_id, agent_type, specialist)
            )
            conn.commit()
            json_output({"id": cur.lastrowid})

        elif action == "complete":
            state_id = int(require_flag(flags, "id"))
            status = require_flag(flags, "status")
            output_path = flags.get("output_path") or None
            conn.execute(
                "UPDATE session_state SET status=?, completed=CURRENT_TIMESTAMP, output_path=? WHERE id=?",
                (status, output_path, state_id)
            )
            conn.commit()
            json_output({"id": state_id, "status": status})

        else:
            print("Usage: db_agent.py start|complete [options]", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
