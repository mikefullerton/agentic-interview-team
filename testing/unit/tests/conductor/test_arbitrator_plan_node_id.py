"""plan_node_id join key: nullable on existing stream tables.

Goal: prove that the new plan_node_id columns are nullable (existing code
works unchanged), are FK-enforced when set, and support cross-stream
filter queries.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA_PATH = (
    Path(__file__).resolve().parents[4]
    / "plugins" / "dev-team" / "services" / "conductor"
    / "arbitrator" / "backends" / "schema.sql"
)


@pytest.fixture
def sqlite_conn(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def seeded(sqlite_conn):
    """One session, one roadmap, one plan_node, ready to reference."""
    now = _now()
    sqlite_conn.execute(
        "INSERT INTO session (session_id, initial_team_id, status, started_at) "
        "VALUES ('s', 't', 'open', ?)", (now,),
    )
    sqlite_conn.execute(
        "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
        "VALUES ('rm', 'r', ?, ?)", (now, now),
    )
    sqlite_conn.execute(
        "INSERT INTO plan_node (node_id, roadmap_id, position, node_kind, title, "
        "creation_date, modification_date) "
        "VALUES ('n1', 'rm', 1.0, 'compound', 'N', ?, ?)", (now, now),
    )
    sqlite_conn.commit()
    return sqlite_conn


def test_message_plan_node_id_defaults_to_null(seeded):
    now = _now()
    seeded.execute(
        "INSERT INTO message (message_id, session_id, team_id, direction, type, "
        "body, creation_date) VALUES ('m1', 's', 't', 'in', 'question', 'hi', ?)",
        (now,),
    )
    seeded.commit()
    row = seeded.execute(
        "SELECT plan_node_id FROM message WHERE message_id='m1'"
    ).fetchone()
    assert row[0] is None


def test_message_plan_node_id_set_works(seeded):
    now = _now()
    seeded.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "direction, type, body, creation_date) "
        "VALUES ('m1', 's', 't', 'n1', 'in', 'question', 'hi', ?)", (now,),
    )
    seeded.commit()
    row = seeded.execute(
        "SELECT plan_node_id FROM message WHERE message_id='m1'"
    ).fetchone()
    assert row[0] == "n1"


def test_message_plan_node_id_fk_rejects_unknown(seeded):
    now = _now()
    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(
            "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
            "direction, type, body, creation_date) "
            "VALUES ('m1', 's', 't', 'does-not-exist', 'in', 'question', 'hi', ?)",
            (now,),
        )


@pytest.mark.parametrize("table,insert_sql", [
    (
        "state",
        "INSERT INTO state (node_id, session_id, team_id, plan_node_id, state_name, "
        "status, entry_date) VALUES ('st', 's', 't', 'n1', 'start', 'active', :now)",
    ),
    (
        "gate",
        "INSERT INTO gate (gate_id, session_id, team_id, plan_node_id, category, "
        "options_json, creation_date) "
        "VALUES ('g', 's', 't', 'n1', 'flow', '[]', :now)",
    ),
    (
        "result",
        "INSERT INTO result (result_id, session_id, team_id, plan_node_id, "
        "specialist_id, passed, summary_json, creation_date) "
        "VALUES ('r', 's', 't', 'n1', 'sp', 1, '{}', :now)",
    ),
    (
        "event",
        "INSERT INTO event (event_id, session_id, plan_node_id, sequence, kind, "
        "payload_json, event_date) VALUES ('e', 's', 'n1', 1, 'lifecycle', '{}', :now)",
    ),
    (
        "task",
        "INSERT INTO task (task_id, session_id, team_id, plan_node_id, kind, "
        "payload_json, status, enqueued_at) "
        "VALUES ('tk', 's', 't', 'n1', 'dispatch', '{}', 'queued', :now)",
    ),
    (
        "request",
        "INSERT INTO request (request_id, session_id, from_team, to_team, plan_node_id, "
        "kind, input_json, status, enqueued_at, timeout_date) "
        "VALUES ('rq', 's', 't', 't', 'n1', 'k', '{}', 'pending', :now, :now)",
    ),
])
def test_plan_node_id_works_on_each_stream(seeded, table, insert_sql):
    now = _now()
    seeded.execute(insert_sql, {"now": now})
    seeded.commit()
    row = seeded.execute(
        f"SELECT plan_node_id FROM {table}"
    ).fetchone()
    assert row[0] == "n1"


def test_cross_stream_filter_returns_all_rows(seeded):
    now = _now()
    # Plant one row per stream, all tagged with plan_node_id='n1'.
    seeded.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, direction, "
        "type, body, creation_date) VALUES ('m', 's', 't', 'n1', 'in', 'q', 'b', ?)", (now,),
    )
    seeded.execute(
        "INSERT INTO event (event_id, session_id, plan_node_id, sequence, kind, "
        "payload_json, event_date) VALUES ('e', 's', 'n1', 1, 'lifecycle', '{}', ?)", (now,),
    )
    seeded.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, plan_node_id, "
        "kind, input_json, status, enqueued_at, timeout_date) "
        "VALUES ('rq', 's', 't', 't', 'n1', 'k', '{}', 'pending', ?, ?)", (now, now),
    )
    seeded.commit()

    rows = seeded.execute("""
        SELECT 'message' AS stream, message_id AS row_id FROM message WHERE plan_node_id='n1'
        UNION ALL
        SELECT 'event',   event_id   FROM event   WHERE plan_node_id='n1'
        UNION ALL
        SELECT 'request', request_id FROM request WHERE plan_node_id='n1'
        ORDER BY stream
    """).fetchall()
    pairs = {(r[0], r[1]) for r in rows}
    assert pairs == {("message", "m"), ("event", "e"), ("request", "rq")}


def test_existing_insert_patterns_still_work(seeded):
    """Old inserts without plan_node_id keep working unchanged."""
    now = _now()
    seeded.execute(
        "INSERT INTO message (message_id, session_id, team_id, direction, type, "
        "body, creation_date) VALUES ('m', 's', 't', 'in', 'q', 'b', ?)", (now,),
    )
    seeded.commit()
    row = seeded.execute(
        "SELECT message_id, plan_node_id FROM message WHERE message_id='m'"
    ).fetchone()
    assert row == ("m", None)
