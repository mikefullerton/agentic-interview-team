"""Live conductor schema carries dispatch + attempt tables with parent_dispatch_id."""
from __future__ import annotations


def test_dispatch_table_exists_with_parent_column(sqlite_conn):
    cols = {
        row[1] for row in sqlite_conn.execute(
            "PRAGMA table_info(dispatch)"
        ).fetchall()
    }
    assert {
        "dispatch_id", "session_id", "team_id", "plan_node_id",
        "parent_dispatch_id", "agent_kind", "agent_name",
        "logical_model", "concrete_model", "status",
        "start_date", "end_date",
    } <= cols


def test_attempt_table_exists(sqlite_conn):
    cols = {
        row[1] for row in sqlite_conn.execute(
            "PRAGMA table_info(attempt)"
        ).fetchall()
    }
    assert {
        "attempt_id", "result_id", "session_id",
        "attempt_kind", "attempt_number",
        "worker_dispatch_id", "verifier_dispatch_id", "verdict",
        "start_date", "end_date",
    } <= cols


def test_parent_dispatch_fk_rejects_unknown(sqlite_conn, iso_now, seed_session):
    import sqlite3
    sess = seed_session(session_id="s-d")
    with __import__("pytest").raises(sqlite3.IntegrityError):
        sqlite_conn.execute(
            "INSERT INTO dispatch "
            "(dispatch_id, session_id, team_id, parent_dispatch_id, "
            " agent_kind, agent_name, logical_model, status, start_date) "
            "VALUES ('d1', ?, 't1', 'ghost', 'worker', 'w', 'balanced', "
            " 'running', ?)",
            (sess, iso_now),
        )


def test_attempt_fk_requires_real_worker_dispatch(sqlite_conn, iso_now, seed_session):
    import sqlite3
    sess = seed_session(session_id="s-a")
    sqlite_conn.execute(
        "INSERT INTO result "
        "(result_id, session_id, team_id, specialist_id, passed, "
        " summary_json, creation_date) "
        "VALUES ('r1', ?, 't1', 'sp', 1, '{}', ?)",
        (sess, iso_now),
    )
    with __import__("pytest").raises(sqlite3.IntegrityError):
        sqlite_conn.execute(
            "INSERT INTO attempt "
            "(attempt_id, result_id, session_id, attempt_kind, "
            " attempt_number, worker_dispatch_id, start_date) "
            "VALUES ('a1', 'r1', ?, 'speciality', 1, 'ghost-w', ?)",
            (sess, iso_now),
        )
