#!/usr/bin/env python3
"""db-message — Log an agent activity message.
Usage: db_message.py --run <id> [--session-state <id>] [--agent-type <type>]
                     [--specialist <domain>] [--persona <name>] --message "<text>"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output


def main():
    init_db()
    flags = parse_flags(sys.argv[1:])

    session_id = int(require_flag(flags, "run"))
    message = require_flag(flags, "message")

    session_state_id = flags.get("session_state") or None
    if session_state_id is not None:
        session_state_id = int(session_state_id)
    agent_type = flags.get("agent_type") or None
    specialist = flags.get("specialist") or None
    persona = flags.get("persona") or None

    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO messages (session_id, session_state_id, agent_type, specialist_domain, persona, message) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, session_state_id, agent_type, specialist, persona, message)
        )
        conn.commit()
        json_output({"id": cur.lastrowid})
    finally:
        conn.close()


if __name__ == "__main__":
    main()
