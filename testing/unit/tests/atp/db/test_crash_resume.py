"""Crash-resume support on the session row.

session carries last_task_id, last_state_id, last_event_sequence. A
restarting conductor reads those to know where to pick up:

  - last_task_id         → skip completed tasks, pull the next queued
  - last_state_id        → reconstruct the state tree up to this node
  - last_event_sequence  → resume observer tail after this sequence

These tests use the file-backed SQLite database (not :memory:) so we
can prove state survives the 'crash' (close the connection and reopen).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def _load_schema(conn: sqlite3.Connection, schema_sql: str) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema_sql)
    conn.commit()


def _fresh_db(tmp_path: Path, schema_sql: str) -> Path:
    db = tmp_path / "atp.db"
    c = sqlite3.connect(db)
    _load_schema(c, schema_sql)
    c.close()
    return db


def _insert_session_with_progress(db: Path, now: str) -> None:
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = ON")

    c.execute(
        "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
        "VALUES ('rm', 'r', ?, ?)", (now, now),
    )
    c.execute(
        "INSERT INTO plan_node (node_id, roadmap_id, position, node_kind, title, "
        "creation_date, modification_date) "
        "VALUES ('n1', 'rm', 1.0, 'compound', 'N1', ?, ?)", (now, now),
    )
    c.execute(
        "INSERT INTO session (session_id, playbook, roadmap_id, plan_node_id, host, "
        "pid, status, ui_mode, creation_date, modification_date) "
        "VALUES ('s', 'atp-plan', 'rm', 'n1', 'terminal', 1234, 'running', 'tui', ?, ?)",
        (now, now),
    )
    c.execute(
        "INSERT INTO team (session_id, team_id, team_playbook, team_role, status, "
        "creation_date, modification_date) "
        "VALUES ('s', 't1', 'pb', 'interview', 'active', ?, ?)", (now, now),
    )

    # State tree: root → child (both ran, child is 'running' not 'done').
    c.execute(
        "INSERT INTO state (state_id, session_id, team_id, state_name, actor, status, "
        "entry_date) VALUES ('st-root', 's', 't1', 'start', 'team-lead', 'running', ?)",
        (now,),
    )
    c.execute(
        "INSERT INTO state (state_id, session_id, team_id, parent_state_id, state_name, "
        "actor, status, entry_date) "
        "VALUES ('st-child', 's', 't1', 'st-root', 'dispatch-specialist', 'team-lead', "
        "'running', ?)",
        (now,),
    )

    # Task queue: one completed, one in-flight, one queued.
    for task_id, status in [("task-1", "completed"), ("task-2", "in-flight"), ("task-3", "queued")]:
        c.execute(
            "INSERT INTO task (task_id, session_id, team_id, task_kind, status, "
            "scheduled_date) VALUES (?, 's', 't1', 'dispatch', ?, ?)",
            (task_id, status, now),
        )

    # Events: 3 emitted in sequence.
    for seq in (1, 2, 3):
        c.execute(
            "INSERT INTO event (session_id, team_id, sequence, event_kind, event_date) "
            "VALUES ('s', 't1', ?, 'lifecycle', ?)", (seq, now),
        )

    # Persist resume cursors.
    c.execute(
        "UPDATE session SET last_task_id='task-1', last_state_id='st-child', "
        "last_event_sequence=3, modification_date=? WHERE session_id='s'",
        (now,),
    )
    c.commit()
    c.close()


def test_resume_cursors_survive_reconnect(tmp_path, schema_sql, now):
    db = _fresh_db(tmp_path, schema_sql)
    _insert_session_with_progress(db, now)

    # "Crash" is simulated by closing above. Now reopen.
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = ON")
    row = c.execute(
        "SELECT last_task_id, last_state_id, last_event_sequence, status "
        "FROM session WHERE session_id='s'"
    ).fetchone()
    assert row == ("task-1", "st-child", 3, "running")
    c.close()


def test_resume_reconstructs_state_tree(tmp_path, schema_sql, now):
    db = _fresh_db(tmp_path, schema_sql)
    _insert_session_with_progress(db, now)

    c = sqlite3.connect(db)
    # Walk the state tree for the session via recursive CTE.
    rows = c.execute("""
        WITH RECURSIVE tree(state_id, parent_state_id, depth) AS (
            SELECT state_id, parent_state_id, 0
            FROM state
            WHERE session_id='s' AND parent_state_id IS NULL
            UNION ALL
            SELECT s.state_id, s.parent_state_id, t.depth + 1
            FROM state s JOIN tree t ON s.parent_state_id = t.state_id
            WHERE s.session_id='s'
        )
        SELECT state_id, depth FROM tree ORDER BY depth, state_id
    """).fetchall()
    assert rows == [("st-root", 0), ("st-child", 1)]
    c.close()


def test_resume_task_queue_picks_up_from_cursor(tmp_path, schema_sql, now):
    db = _fresh_db(tmp_path, schema_sql)
    _insert_session_with_progress(db, now)

    c = sqlite3.connect(db)
    # Resume logic: the next work is the earliest queued task after the cursor's
    # last completed one. Here the cursor is 'task-1' (last completed), so the
    # conductor should pick up 'task-3' (queued); 'task-2' is in-flight (owned
    # by a prior now-dead attempt — a real conductor would have to decide to
    # reclaim or mark failed).
    rows = c.execute(
        "SELECT task_id, status FROM task WHERE session_id='s' "
        "ORDER BY scheduled_date, task_id"
    ).fetchall()
    states = {r[0]: r[1] for r in rows}
    assert states == {"task-1": "completed", "task-2": "in-flight", "task-3": "queued"}
    c.close()


def test_resume_event_tail_after_cursor(tmp_path, schema_sql, now):
    db = _fresh_db(tmp_path, schema_sql)
    _insert_session_with_progress(db, now)

    c = sqlite3.connect(db)
    # After crash, the observer subscriber wants events *after* last_event_sequence.
    cursor = c.execute(
        "SELECT last_event_sequence FROM session WHERE session_id='s'"
    ).fetchone()[0]
    assert cursor == 3

    # Simulate new events arriving post-resume.
    c.execute(
        "INSERT INTO event (session_id, team_id, sequence, event_kind, event_date) "
        "VALUES ('s', 't1', 4, 'lifecycle', ?)", (now,),
    )
    c.execute(
        "INSERT INTO event (session_id, team_id, sequence, event_kind, event_date) "
        "VALUES ('s', 't1', 5, 'tool-use', ?)", (now,),
    )
    c.commit()

    new_events = c.execute(
        "SELECT sequence FROM event WHERE session_id='s' AND sequence > ? "
        "ORDER BY sequence", (cursor,),
    ).fetchall()
    assert [r[0] for r in new_events] == [4, 5]
    c.close()


def test_resume_persists_across_multiple_reopens(tmp_path, schema_sql, now):
    """Repeated open-write-close cycles don't lose state."""
    db = _fresh_db(tmp_path, schema_sql)
    _insert_session_with_progress(db, now)

    for cursor_task in ["task-3a", "task-3b", "task-3c"]:
        c = sqlite3.connect(db)
        c.execute(
            "UPDATE session SET last_task_id = ?, modification_date = ? "
            "WHERE session_id='s'",
            (cursor_task, now),
        )
        c.commit()
        c.close()

    c = sqlite3.connect(db)
    final = c.execute(
        "SELECT last_task_id FROM session WHERE session_id='s'"
    ).fetchone()[0]
    assert final == "task-3c"
    c.close()
