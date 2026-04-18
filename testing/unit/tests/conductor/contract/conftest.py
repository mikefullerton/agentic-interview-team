"""Fixtures for roadmap contract tests.

The parent conductor/conftest.py supplies arb_factory, run_async, session_id,
and backend_factory. This module adds raw-sqlite fixtures that load the
LIVE conductor schema (not the reference schema-v3.sql that atp/db/ uses).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

LIVE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[5]
    / "plugins" / "dev-team" / "services" / "conductor"
    / "arbitrator" / "backends" / "schema.sql"
)


@pytest.fixture
def live_schema_sql() -> str:
    return LIVE_SCHEMA_PATH.read_text()


@pytest.fixture
def sqlite_conn(live_schema_sql):
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(live_schema_sql)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@pytest.fixture
def seed_session(sqlite_conn, iso_now):
    """Insert one session row and return its id. No roadmap linkage by default."""
    def _factory(session_id: str = "sess-c", roadmap_id: str | None = None) -> str:
        sqlite_conn.execute(
            "INSERT INTO session "
            "(session_id, initial_team_id, status, roadmap_id, creation_date) "
            "VALUES (?, 't1', 'open', ?, ?)",
            (session_id, roadmap_id, iso_now),
        )
        sqlite_conn.commit()
        return session_id
    return _factory


@pytest.fixture
def seed_roadmap(sqlite_conn, iso_now):
    """Insert a roadmap and return its id."""
    def _factory(roadmap_id: str = "rm-c", title: str = "Contract Roadmap") -> str:
        sqlite_conn.execute(
            "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?)",
            (roadmap_id, title, iso_now, iso_now),
        )
        sqlite_conn.commit()
        return roadmap_id
    return _factory


@pytest.fixture
def seed_node(sqlite_conn, iso_now):
    """Insert a plan_node and return its id."""
    def _factory(
        node_id: str,
        roadmap_id: str,
        *,
        parent_id: str | None = None,
        position: float = 1.0,
        node_kind: str = "primitive",
        title: str | None = None,
    ) -> str:
        sqlite_conn.execute(
            "INSERT INTO plan_node (node_id, roadmap_id, parent_id, position, "
            "node_kind, title, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (node_id, roadmap_id, parent_id, position, node_kind,
             title or node_id, iso_now, iso_now),
        )
        sqlite_conn.commit()
        return node_id
    return _factory


@pytest.fixture
def add_edge(sqlite_conn, iso_now):
    """Insert a node_dependency edge."""
    def _factory(node_id: str, depends_on_id: str) -> None:
        sqlite_conn.execute(
            "INSERT INTO node_dependency (node_id, depends_on_id, creation_date) "
            "VALUES (?, ?, ?)",
            (node_id, depends_on_id, iso_now),
        )
        sqlite_conn.commit()
    return _factory
