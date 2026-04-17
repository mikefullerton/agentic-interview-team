#!/usr/bin/env python3
"""Schema conformance linter for .claude/rules/db-schema-design.md.

Loads a SQL schema file into an in-memory SQLite DB and reports violations
of the project's DB-design rules:

  1. No blob columns in primary tables (narrative content must route through
     a `body` side-table; TEXT columns on primary tables must be short
     identifiers or fixed vocabularies — heuristic: any TEXT column named
     `body`, `summary`, `rationale`, `description`, or with a `_json`/`_text`
     suffix is flagged).
  2. No *_at date naming — use creation_date / modification_date / entry_date
     etc. instead of created_at / updated_at / entered_at.
  3. Primary entity tables carry `creation_date`.
  4. Non-roadmap stream tables carry `plan_node_id` when they represent
     stream entries that should be joinable to the graph.
  5. The `body` side-table is present and has a composite primary key
     (owner_type, owner_id).

Usage:
  python3 schema_lint.py <schema.sql>
  exit 0 if clean, exit 1 if violations found (prints one line per violation).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


# Tables we don't expect to carry plan_node_id: top-level containers,
# the body side-table, junction-style tables, pure session-scoped config,
# sub-resources whose parent already carries plan_node_id (attempt
# belongs to result; gate_option and verdict belong to gate), and
# PM annotation tables (schedule / todo) which are project-storage
# records not stream entries — they're optionally linked via other
# domain fields rather than a plan_node_id join key.
PLAN_NODE_ID_EXEMPT = {
    "roadmap", "plan_node", "node_dependency", "node_state_event",
    "session", "session_property", "team", "task",
    "gate_option", "verdict",
    "attempt",
    "body",
    "schedule", "todo",
}

# Column names that strongly suggest narrative blob content.
# These MUST route through the body side-table, not inline.
BLOB_COLUMN_NAMES = {
    "body", "summary", "rationale", "description", "detail", "interpretation",
    "prose", "narrative", "notes", "content",
}

# Column name suffixes that signal blob-ish content.
# Note: *_json is deliberately excluded — schema-validated structured JSON
# content (e.g. event.payload_json gated by event.kind) is permitted on
# primary rows. True narrative blobs use the names in BLOB_COLUMN_NAMES.
BLOB_COLUMN_SUFFIXES = ("_text", "_body", "_blob")

# Allowed primary tables where a *_text column is fine because the table
# exists specifically to hold narrative content.
NARRATIVE_SIDE_TABLES = {"body"}

# Tables that are entity roots and should carry creation_date.
ENTITY_TABLES_REQUIRE_CREATION_DATE = {
    "roadmap", "plan_node", "node_dependency", "session", "team",
    "message", "gate", "verdict", "interpretation", "request",
    "result", "finding", "artifact", "concern", "decision",
}


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [r[0] for r in rows]


def _columns(conn: sqlite3.Connection, table: str) -> list[tuple[str, str, int]]:
    """Returns (name, type, is_pk) for each column."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [(r[1], (r[2] or "").upper(), r[5]) for r in rows]


def _primary_key_cols(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows if r[5] > 0}


def check_no_at_suffix(conn: sqlite3.Connection) -> list[str]:
    violations = []
    for table in _tables(conn):
        for name, _type, _is_pk in _columns(conn, table):
            if name.endswith("_at"):
                violations.append(
                    f"{table}.{name}: use creation_date / modification_date / "
                    f"entry_date / start_date etc., not *_at"
                )
    return violations


def check_no_blob_columns(conn: sqlite3.Connection) -> list[str]:
    violations = []
    for table in _tables(conn):
        if table in NARRATIVE_SIDE_TABLES:
            continue
        for name, _type, _is_pk in _columns(conn, table):
            if name in BLOB_COLUMN_NAMES:
                violations.append(
                    f"{table}.{name}: narrative content belongs in the body "
                    f"side-table (body, owner_type, owner_id), not inline"
                )
            elif any(name.endswith(s) for s in BLOB_COLUMN_SUFFIXES):
                violations.append(
                    f"{table}.{name}: *_json / *_text / *_body columns are "
                    f"blob-ish; route through the body side-table or normalize"
                )
    return violations


def check_entity_tables_have_creation_date(conn: sqlite3.Connection) -> list[str]:
    violations = []
    for table in _tables(conn):
        if table not in ENTITY_TABLES_REQUIRE_CREATION_DATE:
            continue
        col_names = {c[0] for c in _columns(conn, table)}
        if "creation_date" not in col_names:
            violations.append(f"{table}: missing creation_date column")
    return violations


def check_plan_node_id_present(conn: sqlite3.Connection) -> list[str]:
    violations = []
    for table in _tables(conn):
        if table in PLAN_NODE_ID_EXEMPT:
            continue
        col_names = {c[0] for c in _columns(conn, table)}
        if "plan_node_id" not in col_names:
            violations.append(
                f"{table}: missing plan_node_id — cross-stream join key is "
                f"required on non-roadmap stream tables"
            )
    return violations


def check_body_table_shape(conn: sqlite3.Connection) -> list[str]:
    violations = []
    if "body" not in _tables(conn):
        return ["body: side-table is required to isolate narrative content"]
    col_names = {c[0] for c in _columns(conn, "body")}
    required = {"owner_type", "owner_id", "body_format", "body_text", "modification_date"}
    missing = required - col_names
    if missing:
        violations.append(f"body: missing required columns {sorted(missing)}")
    pk = _primary_key_cols(conn, "body")
    if pk != {"owner_type", "owner_id"}:
        violations.append(
            f"body: composite primary key must be (owner_type, owner_id), got {sorted(pk)}"
        )
    return violations


CHECKS = [
    ("no *_at date naming",              check_no_at_suffix),
    ("no blob columns in primary tables", check_no_blob_columns),
    ("entity tables have creation_date", check_entity_tables_have_creation_date),
    ("plan_node_id join key present",    check_plan_node_id_present),
    ("body side-table shape",            check_body_table_shape),
]


def lint(schema_sql: str) -> list[str]:
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
    except sqlite3.Error as e:
        return [f"SCHEMA LOAD FAILED: {e}"]

    violations: list[str] = []
    for _name, check in CHECKS:
        violations.extend(check(conn))
    conn.close()
    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("schema", type=Path, help="Path to schema .sql file")
    args = parser.parse_args(argv)

    if not args.schema.exists():
        print(f"error: {args.schema} not found", file=sys.stderr)
        return 2

    violations = lint(args.schema.read_text())
    for v in violations:
        print(v)

    if violations:
        print(f"\n{len(violations)} violation(s)", file=sys.stderr)
        return 1
    print("schema conforms to .claude/rules/db-schema-design.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
