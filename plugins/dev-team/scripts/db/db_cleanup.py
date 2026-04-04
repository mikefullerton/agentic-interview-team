#!/usr/bin/env python3
"""db-cleanup — Age out old sessions and associated data.
Usage: db_cleanup.py --older-than <duration>   e.g. 90d, 6m, 1y

Cascading delete order:
  messages → artifacts → findings (via session_state) → session_state → sessions
Does NOT delete projects.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, json_output


UNIT_MAP = {"d": "days", "m": "months", "y": "years"}


def main():
    init_db()
    flags = parse_flags(sys.argv[1:])

    older_than = flags.get("older_than", "")
    if not older_than:
        print("Error: --older-than <duration> is required (e.g. 90d, 6m, 1y)", file=sys.stderr)
        sys.exit(1)

    m = re.fullmatch(r"(\d+)([dmy])", older_than)
    if not m:
        print(f"Error: invalid duration '{older_than}' — expected integer + unit (d/m/y)", file=sys.stderr)
        sys.exit(1)

    value, unit = m.group(1), m.group(2)
    sqlite_modifier = f"-{value} {UNIT_MAP[unit]}"

    conn = connect()
    try:
        # Collect stale session IDs
        cur = conn.execute(
            "SELECT id FROM sessions WHERE started < datetime('now', ?)",
            (sqlite_modifier,)
        )
        stale_session_ids = [r[0] for r in cur.fetchall()]

        if not stale_session_ids:
            json_output({"deleted": {"messages": 0, "artifacts": 0, "findings": 0, "session_state": 0, "sessions": 0}})
            return

        placeholders = ",".join("?" * len(stale_session_ids))

        # Collect stale session_state IDs
        cur = conn.execute(
            f"SELECT id FROM session_state WHERE session_id IN ({placeholders})",
            stale_session_ids
        )
        stale_state_ids = [r[0] for r in cur.fetchall()]

        # Count before deleting
        cur = conn.execute(
            f"SELECT COUNT(*) FROM messages WHERE session_id IN ({placeholders})",
            stale_session_ids
        )
        msg_count = cur.fetchone()[0]

        cur = conn.execute(
            f"SELECT COUNT(*) FROM artifacts WHERE session_id IN ({placeholders})",
            stale_session_ids
        )
        art_count = cur.fetchone()[0]

        find_count = 0
        ss_count = 0
        if stale_state_ids:
            state_placeholders = ",".join("?" * len(stale_state_ids))
            cur = conn.execute(
                f"SELECT COUNT(*) FROM findings WHERE session_state_id IN ({state_placeholders})",
                stale_state_ids
            )
            find_count = cur.fetchone()[0]
            cur = conn.execute(
                f"SELECT COUNT(*) FROM session_state WHERE id IN ({state_placeholders})",
                stale_state_ids
            )
            ss_count = cur.fetchone()[0]

        session_count = len(stale_session_ids)

        # Cascading deletes
        conn.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", stale_session_ids)
        conn.execute(f"DELETE FROM artifacts WHERE session_id IN ({placeholders})", stale_session_ids)
        if stale_state_ids:
            state_placeholders = ",".join("?" * len(stale_state_ids))
            conn.execute(f"DELETE FROM findings WHERE session_state_id IN ({state_placeholders})", stale_state_ids)
            conn.execute(f"DELETE FROM session_state WHERE id IN ({state_placeholders})", stale_state_ids)
        conn.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", stale_session_ids)
        conn.commit()

        json_output({
            "deleted": {
                "messages": msg_count,
                "artifacts": art_count,
                "findings": find_count,
                "session_state": ss_count,
                "sessions": session_count,
            }
        })
    finally:
        conn.close()


if __name__ == "__main__":
    main()
