#!/usr/bin/env python3
"""db-project — Create or get a project.
Usage: db_project.py --name <name> --path <path>
       db_project.py --get <id>
       db_project.py --list
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output, row_to_dict


def main():
    init_db()
    argv = sys.argv[1:]

    action = ""
    extra_argv = []
    project_id = ""

    # Detect action from flags
    i = 0
    while i < len(argv):
        if argv[i] == "--name":
            action = "upsert"
            extra_argv.append(argv[i])
            if i + 1 < len(argv):
                extra_argv.append(argv[i + 1])
                i += 2
            else:
                i += 1
        elif argv[i] == "--get":
            action = "get"
            if i + 1 < len(argv):
                project_id = argv[i + 1]
                i += 2
            else:
                i += 1
        elif argv[i] == "--list":
            action = "list"
            i += 1
        else:
            extra_argv.append(argv[i])
            i += 1

    flags = parse_flags(extra_argv + argv)

    conn = connect()
    try:
        if action == "upsert":
            name = require_flag(flags, "name")
            path = flags.get("path", "")
            cur = conn.execute("SELECT id FROM projects WHERE name=? LIMIT 1", (name,))
            row = cur.fetchone()
            if row:
                pid = row[0]
                conn.execute(
                    "UPDATE projects SET path=?, modified=CURRENT_TIMESTAMP WHERE id=?",
                    (path, pid)
                )
                conn.commit()
                json_output({"id": pid})
            else:
                cur = conn.execute(
                    "INSERT INTO projects (name, path) VALUES (?, ?)",
                    (name, path)
                )
                conn.commit()
                json_output({"id": cur.lastrowid})

        elif action == "get":
            if not project_id:
                print("Missing required flag: --get <id>", file=sys.stderr)
                sys.exit(1)
            cur = conn.execute("SELECT * FROM projects WHERE id=?", (int(project_id),))
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        elif action == "list":
            cur = conn.execute("SELECT * FROM projects ORDER BY modified DESC")
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        else:
            print("Usage: db_project.py --name <name> --path <path> | --get <id> | --list", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
