"""schema-v3.sql loads cleanly and declares the tables + FKs we expect."""
from __future__ import annotations

import sqlite3

import pytest


EXPECTED_TABLES = {
    # Roadmap
    "roadmap", "plan_node", "node_dependency", "node_state_event",
    # Session & runtime
    "session", "session_property", "team", "state", "task",
    # Transcript
    "message", "gate", "gate_option", "verdict", "interpretation",
    # Requests
    "request",
    # Observer + retry
    "dispatch", "attempt", "event",
    # Results
    "result", "finding", "artifact",
    # Annotations
    "concern", "decision",
    # Body side-table
    "body",
}

# Streams that should all carry plan_node_id as the cross-stream join key.
EXPECTED_PLAN_NODE_ID_COLUMNS = {
    "message", "gate", "interpretation", "request", "dispatch",
    "event", "state", "result", "finding", "artifact",
    "concern", "decision",
}


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _foreign_keys(conn: sqlite3.Connection, table: str) -> list[tuple[str, str, str]]:
    """Returns (from_col, target_table, target_col) tuples."""
    rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    return [(r[3], r[2], r[4]) for r in rows]


def test_all_expected_tables_exist(conn):
    actual = _tables(conn)
    missing = EXPECTED_TABLES - actual
    assert not missing, f"missing tables: {missing}"


def test_no_unexpected_tables(conn):
    actual = _tables(conn)
    extra = actual - EXPECTED_TABLES - {"sqlite_sequence"}  # autoincrement metadata
    assert not extra, f"unexpected tables: {extra}"


def test_plan_node_id_present_on_cross_stream_tables(conn):
    for table in EXPECTED_PLAN_NODE_ID_COLUMNS:
        cols = _column_names(conn, table)
        assert "plan_node_id" in cols, f"{table} missing plan_node_id join key"


def test_plan_node_id_is_fk_to_plan_node(conn):
    for table in EXPECTED_PLAN_NODE_ID_COLUMNS:
        fks = _foreign_keys(conn, table)
        plan_node_fk = [fk for fk in fks if fk[0] == "plan_node_id"]
        assert plan_node_fk, f"{table}.plan_node_id is not declared as a FK"
        _, target_table, target_col = plan_node_fk[0]
        assert target_table == "plan_node"
        assert target_col == "node_id"


def test_body_side_table_has_composite_primary_key(conn):
    rows = conn.execute("PRAGMA table_info(body)").fetchall()
    pk_cols = [r[1] for r in rows if r[5] > 0]
    assert set(pk_cols) == {"owner_type", "owner_id"}


def test_node_dependency_unique_constraint(conn, make_roadmap, make_node, add_dependency):
    rm = make_roadmap()
    make_node("a", rm, position=1)
    make_node("b", rm, position=2)
    add_dependency("a", "b")
    with pytest.raises(sqlite3.IntegrityError):
        add_dependency("a", "b")  # duplicate edge


def test_foreign_keys_are_enforced(conn, now):
    with pytest.raises(sqlite3.IntegrityError):
        # roadmap_id points at nonexistent roadmap
        conn.execute(
            "INSERT INTO plan_node (node_id, roadmap_id, position, node_kind, "
            "title, creation_date, modification_date) "
            "VALUES ('orphan', 'no-such-roadmap', 1.0, 'compound', 'x', ?, ?)",
            (now, now),
        )


def test_plan_node_self_reference_fk(conn, make_roadmap, now):
    rm = make_roadmap()
    with pytest.raises(sqlite3.IntegrityError):
        # parent_id points at nonexistent node
        conn.execute(
            "INSERT INTO plan_node (node_id, roadmap_id, parent_id, position, "
            "node_kind, title, creation_date, modification_date) "
            "VALUES ('child', ?, 'no-such-parent', 1.0, 'compound', 'c', ?, ?)",
            (rm, now, now),
        )


def test_required_date_columns_present(conn):
    """Every primary table that represents a created-then-possibly-modified
    entity should have creation_date. Exceptions: append-only logs (which have
    event_date), pure junction tables, and entities that track entry/exit or
    start/end."""
    expected_creation_date = {
        "roadmap", "plan_node", "node_dependency", "session", "team",
        "message", "gate", "gate_option",  # gate_option has position; skip
        "verdict", "interpretation", "request", "result", "finding",
        "artifact", "concern", "decision",
    }
    # gate_option has no creation_date (ordering via position is enough)
    expected_creation_date.discard("gate_option")
    for table in expected_creation_date:
        cols = _column_names(conn, table)
        assert "creation_date" in cols, f"{table} missing creation_date"


def test_no_created_at_naming(conn):
    """The project uses creation_date, not created_at. Verify no *_at columns
    for creation/modification (entry_date, exit_date, start_date, end_date,
    event_date, scheduled_date, started_date, completion_date, verdict_date,
    modification_date, timeout_date, and analogous are permitted)."""
    forbidden_suffixes = ("_at",)  # created_at, updated_at, etc.
    for table in EXPECTED_TABLES:
        cols = _column_names(conn, table)
        bad = [c for c in cols if c.endswith(forbidden_suffixes)]
        assert not bad, f"{table} uses *_at naming: {bad}"


def test_body_table_holds_narrative_not_primary_rows(conn, now):
    """Narrative content routes through body(owner_type, owner_id), not inline."""
    # Insert a body row for a hypothetical plan_node.
    # First create the plan_node so FK works (body doesn't FK owner_id —
    # that's intentional since owner_type varies).
    conn.execute(
        "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
        "VALUES ('rm', 't', ?, ?)", (now, now),
    )
    conn.execute(
        "INSERT INTO plan_node (node_id, roadmap_id, position, node_kind, "
        "title, creation_date, modification_date) "
        "VALUES ('n1', 'rm', 1.0, 'compound', 'T', ?, ?)", (now, now),
    )
    conn.execute(
        "INSERT INTO body (owner_type, owner_id, body_format, body_text, modification_date) "
        "VALUES ('plan_node', 'n1', 'markdown', '# Body content', ?)", (now,),
    )
    conn.commit()

    row = conn.execute(
        "SELECT body_text FROM body WHERE owner_type='plan_node' AND owner_id='n1'"
    ).fetchone()
    assert row[0] == "# Body content"
