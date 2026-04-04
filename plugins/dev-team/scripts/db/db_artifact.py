#!/usr/bin/env python3
"""db-artifact — Write or query artifacts (stores full file content).
Usage: db_artifact.py write --project <id> [--run <id>] [--session-state <id>] --path <path> --category <cat> [--specialist <domain>]
       db_artifact.py get --id <id>
       db_artifact.py search --project <id> [--category <cat>] [--specialist <domain>] [--text <search>]
"""

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import connect, init_db, parse_flags, require_flag, json_output, row_to_dict


def parse_frontmatter(content: str) -> tuple[str, dict, str]:
    """Return (title, frontmatter_dict, body) from a markdown file with YAML frontmatter."""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", {}, content

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return "", {}, content

    fm_lines = lines[1:end]
    body = "".join(lines[end + 1:])

    fm: dict = {}
    for line in fm_lines:
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')

    title = fm.get("title", "")
    return title, fm, body


def main():
    init_db()
    argv = sys.argv[1:]

    action = ""
    if argv and argv[0] in ("write", "get", "search"):
        action = argv[0]
        argv = argv[1:]

    flags = parse_flags(argv)

    conn = connect()
    try:
        if action == "write":
            file_path = require_flag(flags, "path")
            project_id = int(require_flag(flags, "project"))
            category = require_flag(flags, "category")

            fp = Path(file_path)
            if not fp.exists():
                print(f"File not found: {file_path}", file=sys.stderr)
                sys.exit(1)

            raw = fp.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(fp.read_bytes()).hexdigest()
            title, fm_dict, body = parse_frontmatter(raw)
            frontmatter_json = json.dumps(fm_dict)
            rel_path = fp.name

            session_id = flags.get("run") or None
            if session_id is not None:
                session_id = int(session_id)
            session_state_id = flags.get("session_state") or None
            if session_state_id is not None:
                session_state_id = int(session_state_id)
            specialist = flags.get("specialist") or None

            # Check for existing artifact at this path+project
            cur = conn.execute(
                "SELECT id, version FROM artifacts WHERE path=? AND project_id=? ORDER BY version DESC LIMIT 1",
                (file_path, project_id)
            )
            existing = cur.fetchone()

            if existing:
                old_id = existing[0]
                new_version = existing[1] + 1
                conn.execute(
                    "UPDATE artifacts SET content=?, content_hash=?, version=?, modified=CURRENT_TIMESTAMP, "
                    "frontmatter_json=?, title=? WHERE id=?",
                    (body, content_hash, new_version, frontmatter_json, title, old_id)
                )
                conn.commit()
                json_output({"id": old_id, "version": new_version})
            else:
                cur = conn.execute(
                    "INSERT INTO artifacts (project_id, session_id, session_state_id, path, relative_path, "
                    "category, title, specialist, frontmatter_json, content, content_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (project_id, session_id, session_state_id, file_path, rel_path,
                     category, title, specialist, frontmatter_json, body, content_hash)
                )
                conn.commit()
                json_output({"id": cur.lastrowid})

        elif action == "get":
            artifact_id = int(require_flag(flags, "id"))
            cur = conn.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,))
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        elif action == "search":
            project_id = int(require_flag(flags, "project"))
            sql = ("SELECT id, project_id, path, category, title, specialist, version, created, modified "
                   "FROM artifacts WHERE project_id=?")
            params: list = [project_id]
            if flags.get("category"):
                sql += " AND category=?"
                params.append(flags["category"])
            if flags.get("specialist"):
                sql += " AND specialist=?"
                params.append(flags["specialist"])
            if flags.get("text"):
                sql += " AND content LIKE ?"
                params.append(f"%{flags['text']}%")
            sql += " ORDER BY modified DESC"
            cur = conn.execute(sql, params)
            rows = [row_to_dict(r) for r in cur.fetchall()]
            json_output(rows)

        else:
            print("Usage: db_artifact.py write|get|search [options]", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
