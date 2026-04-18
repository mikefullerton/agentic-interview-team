"""Given rows across every stream tagged with plan_node_id='target', a single
UNION query returns them all. Streams covered (live conductor schema):

    state, message, gate, result, finding, event, task, request, decision

Dispatch and attempt tables aren't in the live schema yet — see the Scope
Notes section of docs/planning/2026-04-17-atp-roadmap-contract-tests.md.
"""
from __future__ import annotations


def _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node):
    rm = seed_roadmap(roadmap_id="rm-x")
    seed_node("target", rm, position=1.0)
    seed_node("other",  rm, position=2.0)
    sess = seed_session(session_id="sess-x", roadmap_id=rm)
    return rm, sess


def test_cross_stream_union_returns_every_tagged_row(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    rm, sess = _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node)

    # One row per stream, all tagged with plan_node_id='target'.
    sqlite_conn.execute(
        "INSERT INTO state (node_id, session_id, team_id, plan_node_id, "
        "state_name, status, entry_date) "
        "VALUES ('st1', ?, 't1', 'target', 's', 'active', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "direction, type, creation_date) "
        "VALUES ('m1', ?, 't1', 'target', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO gate (gate_id, session_id, team_id, plan_node_id, category, "
        "options_json, creation_date) "
        "VALUES ('g1', ?, 't1', 'target', 'flow', '[]', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO result (result_id, session_id, team_id, plan_node_id, "
        "specialist_id, passed, summary_json, creation_date) "
        "VALUES ('res1', ?, 't1', 'target', 'sp', 1, '{}', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO finding (finding_id, result_id, plan_node_id, kind, "
        "severity, creation_date) "
        "VALUES ('f1', 'res1', 'target', 'note', 'info', ?)",
        (iso_now,),
    )
    sqlite_conn.execute(
        "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
        "sequence, kind, payload_json, event_date) "
        "VALUES ('e1', ?, 't1', 'target', 1, 'lifecycle', '{}', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO task (task_id, session_id, team_id, plan_node_id, kind, "
        "payload_json, status, scheduled_date) "
        "VALUES ('tk1', ?, 't1', 'target', 'dispatch', '{}', 'pending', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, kind, input_json, status, creation_date, timeout_date) "
        "VALUES ('rq1', ?, 't1', 't2', 'target', 'k', '{}', 'pending', ?, ?)",
        (sess, iso_now, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO decision (decision_id, session_id, team_id, plan_node_id, "
        "title, creation_date) "
        "VALUES ('d1', ?, 't1', 'target', 'use X', ?)",
        (sess, iso_now),
    )

    # Noise: 'other'-tagged + NULL rows that the filter must exclude.
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "direction, type, creation_date) "
        "VALUES ('m-other', ?, 't1', 'other', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, direction, "
        "type, creation_date) "
        "VALUES ('m-null', ?, 't1', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.commit()

    query = """
        SELECT 'state'    AS stream, node_id     AS row_id FROM state    WHERE plan_node_id = :node
        UNION ALL
        SELECT 'message',  message_id  FROM message  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'gate',     gate_id     FROM gate     WHERE plan_node_id = :node
        UNION ALL
        SELECT 'result',   result_id   FROM result   WHERE plan_node_id = :node
        UNION ALL
        SELECT 'finding',  finding_id  FROM finding  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'event',    event_id    FROM event    WHERE plan_node_id = :node
        UNION ALL
        SELECT 'task',     task_id     FROM task     WHERE plan_node_id = :node
        UNION ALL
        SELECT 'request',  request_id  FROM request  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'decision', decision_id FROM decision WHERE plan_node_id = :node
        ORDER BY stream, row_id
    """
    pairs = {(r[0], r[1]) for r in sqlite_conn.execute(query, {"node": "target"}).fetchall()}
    assert pairs == {
        ("state",    "st1"),
        ("message",  "m1"),
        ("gate",     "g1"),
        ("result",   "res1"),
        ("finding",  "f1"),
        ("event",    "e1"),
        ("task",     "tk1"),
        ("request",  "rq1"),
        ("decision", "d1"),
    }

    # 'other' filter returns only the one message tagged with 'other'.
    other = sqlite_conn.execute(query, {"node": "other"}).fetchall()
    assert other == [("message", "m-other")]


def test_per_stream_counts_via_group_by(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    rm, sess = _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node)

    for i in range(3):
        sqlite_conn.execute(
            "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
            "direction, type, creation_date) "
            "VALUES (?, ?, 't1', 'target', 'in', 'question', ?)",
            (f"m{i}", sess, iso_now),
        )
    for i in range(2):
        sqlite_conn.execute(
            "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
            "sequence, kind, payload_json, event_date) "
            "VALUES (?, ?, 't1', 'target', ?, 'lifecycle', '{}', ?)",
            (f"e{i}", sess, i + 1, iso_now),
        )
    sqlite_conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, kind, input_json, status, creation_date, timeout_date) "
        "VALUES ('rq1', ?, 't1', 't2', 'target', 'k', '{}', 'pending', ?, ?)",
        (sess, iso_now, iso_now),
    )
    sqlite_conn.commit()

    counts = dict(sqlite_conn.execute("""
        SELECT stream, COUNT(*) FROM (
            SELECT 'message' AS stream FROM message WHERE plan_node_id='target'
            UNION ALL
            SELECT 'event'             FROM event   WHERE plan_node_id='target'
            UNION ALL
            SELECT 'request'           FROM request WHERE plan_node_id='target'
        ) GROUP BY stream
    """).fetchall())
    assert counts == {"message": 3, "event": 2, "request": 1}


def test_unknown_plan_node_id_rejected_on_every_stream(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    """FK enforcement: no stream accepts an unknown plan_node_id."""
    import sqlite3
    seed_roadmap(roadmap_id="rm-fk")
    sess = seed_session(session_id="sess-fk")

    inserts = [
        ("state", "INSERT INTO state (node_id, session_id, team_id, plan_node_id, "
                  "state_name, status, entry_date) "
                  "VALUES ('st', ?, 't1', 'ghost', 's', 'active', ?)"),
        ("message", "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
                    "direction, type, creation_date) "
                    "VALUES ('m', ?, 't1', 'ghost', 'in', 'q', ?)"),
        ("event", "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
                  "sequence, kind, payload_json, event_date) "
                  "VALUES ('e', ?, 't1', 'ghost', 1, 'lifecycle', '{}', ?)"),
        ("task", "INSERT INTO task (task_id, session_id, team_id, plan_node_id, kind, "
                 "payload_json, status, scheduled_date) "
                 "VALUES ('tk', ?, 't1', 'ghost', 'dispatch', '{}', 'pending', ?)"),
        ("decision", "INSERT INTO decision (decision_id, session_id, team_id, plan_node_id, "
                     "title, creation_date) "
                     "VALUES ('d', ?, 't1', 'ghost', 'x', ?)"),
    ]

    for _table, sql in inserts:
        with __import__("pytest").raises(sqlite3.IntegrityError):
            sqlite_conn.execute(sql, (sess, iso_now))
