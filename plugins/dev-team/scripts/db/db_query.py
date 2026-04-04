#!/usr/bin/env python3
"""db-query — Run ad-hoc SQL against the dev-team database.
Usage: db_query.py "<sql>"           — JSON output
       db_query.py --table "<sql>"   — formatted table output (tab-separated)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, json_output, row_to_dict


def main():
    init_db()
    argv = sys.argv[1:]

    fmt = "json"
    sql = ""

    for arg in argv:
        if arg == "--table":
            fmt = "table"
        elif not arg.startswith("--"):
            sql = arg
        elif arg == "--format" and argv.index(arg) + 1 < len(argv):
            fmt_val = argv[argv.index(arg) + 1]
            if fmt_val == "table":
                fmt = "table"

    if not sql:
        print('Usage: db_query.py [--table] "<sql>"', file=sys.stderr)
        sys.exit(1)

    conn = connect()
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()

        if fmt == "table":
            if rows:
                col_names = [d[0] for d in cur.description]
                print("\t".join(col_names))
                for row in rows:
                    print("\t".join(str(v) if v is not None else "" for v in row))
        else:
            json_output([row_to_dict(r) for r in rows])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
