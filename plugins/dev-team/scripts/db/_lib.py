#!/usr/bin/env python3
"""Shared helpers for database scripts."""

import json
import os
import sqlite3
import sys
from pathlib import Path


def get_db_path() -> Path:
    return Path(os.environ.get(
        "DEVTEAM_DB_PATH",
        os.path.expanduser("~/.agentic-cookbook/dev-team/dev-team.db")
    ))


def get_schema_path() -> Path:
    return Path(__file__).parent / "schema.sql"


def connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    schema = get_schema_path().read_text()
    conn = connect()
    conn.executescript(schema)
    # Check/set schema version
    SCHEMA_VERSION = "1"
    cur = conn.execute("SELECT value FROM meta WHERE key='schema_version'")
    row = cur.fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,)
        )
        conn.commit()
    elif row[0] != SCHEMA_VERSION:
        conn.execute(
            "UPDATE meta SET value=? WHERE key='schema_version'",
            (SCHEMA_VERSION,)
        )
        conn.commit()
        print(f"Migrated database schema from v{row[0]} to v{SCHEMA_VERSION}", file=sys.stderr)
    conn.close()


def parse_flags(argv: list[str]) -> dict[str, str]:
    flags: dict[str, str] = {}
    flag_map = {
        "--project": "project", "--run": "run", "--agent": "agent",
        "--specialist": "specialist", "--id": "id", "--status": "status",
        "--output-path": "output_path", "--name": "name", "--path": "path",
        "--type": "type", "--severity": "severity", "--description": "description",
        "--message": "message", "--category": "category",
        "--artifact-path": "artifact_path", "--content": "content",
        "--format": "format", "--workflow": "workflow", "--days": "days",
        "--session-state": "session_state", "--older-than": "older_than",
        "--text": "text", "--agent-type": "agent_type", "--persona": "persona",
    }
    i = 0
    while i < len(argv):
        if argv[i] in flag_map and i + 1 < len(argv):
            flags[flag_map[argv[i]]] = argv[i + 1]
            i += 2
        else:
            i += 1
    return flags


def require_flag(flags: dict[str, str], name: str) -> str:
    val = flags.get(name, "")
    if not val:
        print(f"Missing required flag: --{name.replace('_', '-')}", file=sys.stderr)
        sys.exit(1)
    return val


def json_output(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, default=str))


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)
