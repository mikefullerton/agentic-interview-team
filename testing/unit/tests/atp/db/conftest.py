"""Shared fixtures for atp schema-v3 tests.

The schema under test is a reference schema, not a live backend. Each test
gets a fresh in-memory SQLite connection with foreign keys enforced.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_PATH = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db" / "schema-v3.sql"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@pytest.fixture
def schema_sql() -> str:
    """The raw DDL from schema-v3.sql."""
    return SCHEMA_PATH.read_text()


@pytest.fixture
def conn(schema_sql: str):
    """Fresh in-memory SQLite with schema loaded and FKs enforced."""
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(schema_sql)
    c.commit()
    yield c
    c.close()


@pytest.fixture
def now() -> str:
    """Current UTC timestamp as ISO-8601 string (DATETIME-compatible)."""
    return _utc_now_iso()


@pytest.fixture
def make_roadmap(conn, now):
    """Factory: insert a roadmap and return its id."""
    def _factory(roadmap_id: str = "rm-test", title: str = "Test Roadmap") -> str:
        conn.execute(
            "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?)",
            (roadmap_id, title, now, now),
        )
        conn.commit()
        return roadmap_id
    return _factory


@pytest.fixture
def make_node(conn, now):
    """Factory: insert a plan_node and return its id."""
    def _factory(
        node_id: str,
        roadmap_id: str,
        parent_id: str | None = None,
        position: float = 1.0,
        node_kind: str = "compound",
        title: str | None = None,
        specialist: str | None = None,
        speciality: str | None = None,
    ) -> str:
        conn.execute(
            "INSERT INTO plan_node (node_id, roadmap_id, parent_id, position, "
            "node_kind, title, specialist, speciality, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                node_id,
                roadmap_id,
                parent_id,
                position,
                node_kind,
                title or node_id,
                specialist,
                speciality,
                now,
                now,
            ),
        )
        conn.commit()
        return node_id
    return _factory


@pytest.fixture
def make_session(conn, now):
    """Factory: insert a session and return its id."""
    def _factory(
        session_id: str = "sess-test",
        playbook: str = "atp-plan",
        roadmap_id: str | None = None,
        plan_node_id: str | None = None,
        status: str = "running",
    ) -> str:
        conn.execute(
            "INSERT INTO session (session_id, playbook, roadmap_id, plan_node_id, "
            "host, status, ui_mode, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, playbook, roadmap_id, plan_node_id, "terminal", status, "tui", now, now),
        )
        conn.commit()
        return session_id
    return _factory


@pytest.fixture
def add_dependency(conn, now):
    """Factory: insert a node_dependency edge."""
    def _factory(node_id: str, depends_on_id: str) -> None:
        conn.execute(
            "INSERT INTO node_dependency (node_id, depends_on_id, creation_date) "
            "VALUES (?, ?, ?)",
            (node_id, depends_on_id, now),
        )
        conn.commit()
    return _factory
