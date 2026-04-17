"""plan_node_id as the cross-stream join key.

Given a mix of rows (messages, events, requests, state, results, findings)
tagged with the same plan_node_id, a single UNION query returns all of
them — the "show me everything about this node" pattern.
"""
from __future__ import annotations


def _seed_common(make_roadmap, make_node, make_session):
    rm = make_roadmap(roadmap_id="rm-x")
    make_node("target", rm, position=1.0, node_kind="primitive")
    make_node("other",  rm, position=2.0, node_kind="primitive")
    sess = make_session(session_id="sess-x", roadmap_id=rm, plan_node_id="target")
    return rm, sess


def test_cross_stream_filter_returns_all_rows(conn, make_roadmap, make_node, make_session, now):
    rm, sess = _seed_common(make_roadmap, make_node, make_session)

    # Plant one row per stream linked to 'target'.
    conn.execute(
        "INSERT INTO team (session_id, team_id, team_playbook, team_role, status, "
        "creation_date, modification_date) VALUES (?, 't1', 'pb', 'executor', 'active', ?, ?)",
        (sess, now, now),
    )
    conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "from_actor, to_actor, message_type, creation_date) "
        "VALUES ('m1', ?, 't1', 'target', 'user', 'team-lead', 'question', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO dispatch (dispatch_id, session_id, team_id, plan_node_id, "
        "agent_kind, agent_name, logical_model, status, start_date) "
        "VALUES ('d1', ?, 't1', 'target', 'speciality-worker', 'editor-worker', "
        "'high-reasoning', 'running', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO event (session_id, team_id, plan_node_id, dispatch_id, "
        "sequence, event_kind, event_date) "
        "VALUES (?, 't1', 'target', 'd1', 1, 'tool-use', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, request_kind, status, timeout_date, creation_date) "
        "VALUES ('r1', ?, 't1', 't1', 'target', 'execution.realize-node', "
        "'pending', ?, ?)",
        (sess, now, now),
    )
    conn.execute(
        "INSERT INTO state (state_id, session_id, team_id, plan_node_id, "
        "state_name, actor, status, entry_date) "
        "VALUES ('s1', ?, 't1', 'target', 'dispatching', 'team-lead', 'running', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO result (result_id, session_id, team_id, specialist, "
        "plan_node_id, status, creation_date) "
        "VALUES ('res1', ?, 't1', 'software-architecture', 'target', 'pass', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO finding (finding_id, result_id, plan_node_id, finding_kind, "
        "severity, creation_date) "
        "VALUES ('f1', 'res1', 'target', 'recommendation', 'low', ?)",
        (now,),
    )

    # Also plant rows tagged with 'other' and rows with NULL plan_node_id —
    # the filter must exclude both.
    conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "from_actor, to_actor, message_type, creation_date) "
        "VALUES ('m2', ?, 't1', 'other', 'user', 'team-lead', 'question', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "from_actor, to_actor, message_type, creation_date) "
        "VALUES ('m3', ?, 't1', NULL, 'user', 'team-lead', 'question', ?)",
        (sess, now),
    )
    conn.commit()

    # The cross-stream filter: a single query showing every row tagged with
    # plan_node_id='target'. Returns (stream, row_id) pairs.
    query = """
        SELECT 'message'  AS stream, message_id  AS row_id FROM message  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'dispatch', dispatch_id FROM dispatch WHERE plan_node_id = :node
        UNION ALL
        SELECT 'event',    CAST(event_id AS TEXT) FROM event WHERE plan_node_id = :node
        UNION ALL
        SELECT 'request',  request_id FROM request WHERE plan_node_id = :node
        UNION ALL
        SELECT 'state',    state_id FROM state WHERE plan_node_id = :node
        UNION ALL
        SELECT 'result',   result_id FROM result WHERE plan_node_id = :node
        UNION ALL
        SELECT 'finding',  finding_id FROM finding WHERE plan_node_id = :node
        ORDER BY stream, row_id
    """
    rows = conn.execute(query, {"node": "target"}).fetchall()
    pairs = {(r[0], r[1]) for r in rows}

    assert pairs == {
        ("message",  "m1"),
        ("dispatch", "d1"),
        ("event",    "1"),
        ("request",  "r1"),
        ("state",    "s1"),
        ("result",   "res1"),
        ("finding",  "f1"),
    }

    # Verify filter excludes rows tagged with other nodes or with NULL.
    other_rows = conn.execute(query, {"node": "other"}).fetchall()
    assert len(other_rows) == 1
    assert other_rows[0] == ("message", "m2")


def test_per_node_observability_counts(conn, make_roadmap, make_node, make_session, now):
    """Per-node observability: count rows per stream in a single query."""
    rm, sess = _seed_common(make_roadmap, make_node, make_session)
    conn.execute(
        "INSERT INTO team (session_id, team_id, team_playbook, team_role, status, "
        "creation_date, modification_date) VALUES (?, 't1', 'pb', 'executor', 'active', ?, ?)",
        (sess, now, now),
    )

    # 3 messages, 2 events, 1 request — all tagged with 'target'.
    for i in range(3):
        conn.execute(
            "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
            "from_actor, to_actor, message_type, creation_date) "
            "VALUES (?, ?, 't1', 'target', 'user', 'team-lead', 'question', ?)",
            (f"m{i}", sess, now),
        )
    conn.execute(
        "INSERT INTO dispatch (dispatch_id, session_id, team_id, plan_node_id, "
        "agent_kind, agent_name, logical_model, status, start_date) "
        "VALUES ('d1', ?, 't1', 'target', 'speciality-worker', 'w', 'balanced', 'done', ?)",
        (sess, now),
    )
    for i in range(2):
        conn.execute(
            "INSERT INTO event (session_id, team_id, plan_node_id, dispatch_id, "
            "sequence, event_kind, event_date) "
            "VALUES (?, 't1', 'target', 'd1', ?, 'tool-use', ?)",
            (sess, i, now),
        )
    conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, request_kind, status, timeout_date, creation_date) "
        "VALUES ('r1', ?, 't1', 't1', 'target', 'k', 'pending', ?, ?)",
        (sess, now, now),
    )
    conn.commit()

    counts = dict(conn.execute("""
        SELECT stream, COUNT(*) FROM (
            SELECT 'message'  AS stream FROM message  WHERE plan_node_id='target'
            UNION ALL
            SELECT 'event'            FROM event    WHERE plan_node_id='target'
            UNION ALL
            SELECT 'request'          FROM request  WHERE plan_node_id='target'
        ) GROUP BY stream
    """).fetchall())

    assert counts == {"message": 3, "event": 2, "request": 1}


def test_cross_stream_attribution_through_join(
    conn, make_roadmap, make_node, make_session, now
):
    """Even attempt rows (which don't carry plan_node_id) are joinable via
    their parent result's plan_node_id."""
    rm, sess = _seed_common(make_roadmap, make_node, make_session)
    conn.execute(
        "INSERT INTO team (session_id, team_id, team_playbook, team_role, status, "
        "creation_date, modification_date) VALUES (?, 't1', 'pb', 'executor', 'active', ?, ?)",
        (sess, now, now),
    )
    conn.execute(
        "INSERT INTO result (result_id, session_id, team_id, specialist, plan_node_id, "
        "status, creation_date) VALUES ('res1', ?, 't1', 'architecture', 'target', 'pass', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO dispatch (dispatch_id, session_id, team_id, plan_node_id, "
        "agent_kind, agent_name, logical_model, status, start_date) "
        "VALUES ('d-w', ?, 't1', 'target', 'speciality-worker', 'w', 'balanced', 'done', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO dispatch (dispatch_id, session_id, team_id, plan_node_id, "
        "agent_kind, agent_name, logical_model, status, start_date) "
        "VALUES ('d-v', ?, 't1', 'target', 'speciality-verifier', 'v', 'balanced', 'done', ?)",
        (sess, now),
    )
    conn.execute(
        "INSERT INTO attempt (attempt_id, result_id, session_id, attempt_kind, "
        "owner_name, attempt_number, worker_dispatch_id, verifier_dispatch_id, "
        "verdict, start_date) "
        "VALUES ('a1', 'res1', ?, 'speciality', 'markdown-editing', 1, 'd-w', 'd-v', 'pass', ?)",
        (sess, now),
    )
    conn.commit()

    # Find all attempts attached (transitively) to 'target'.
    rows = conn.execute("""
        SELECT a.attempt_id, a.attempt_number, a.verdict
        FROM attempt a
        JOIN result r ON a.result_id = r.result_id
        WHERE r.plan_node_id = 'target'
    """).fetchall()
    assert rows == [("a1", 1, "pass")]
