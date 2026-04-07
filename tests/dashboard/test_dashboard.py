"""Tests for the Flask dashboard service."""

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins" / "dev-team" / "services"))

from dashboard.app import create_app
from dashboard import db, models


# ---------------------------------------------------------------------------
# Shared in-memory database fixture
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    workflow TEXT,
    status TEXT,
    started TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS session_state (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    agent_type TEXT,
    specialist_domain TEXT,
    status TEXT,
    started TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    content TEXT,
    role TEXT,
    created TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY,
    session_state_id INTEGER NOT NULL,
    title TEXT,
    severity TEXT,
    created TEXT,
    FOREIGN KEY (session_state_id) REFERENCES session_state(id)
);

CREATE TABLE IF NOT EXISTS specialist_assignments (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    specialist TEXT,
    tier INTEGER
);
"""


def make_conn():
    """Create a fresh writable in-memory connection with schema and seed data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    # Projects
    conn.execute("INSERT INTO projects VALUES (1, 'Zeta Project')")
    conn.execute("INSERT INTO projects VALUES (2, 'Alpha Project')")

    # Sessions
    conn.execute(
        "INSERT INTO sessions VALUES (10, 1, 'discovery', 'running', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO sessions VALUES (20, 2, 'analysis', 'completed', '2026-01-02T09:00:00')"
    )

    # session_state rows for session 10
    conn.execute(
        "INSERT INTO session_state VALUES (100, 10, 'team-lead', NULL, 'completed', '2026-01-01T10:01:00')"
    )
    conn.execute(
        "INSERT INTO session_state VALUES (101, 10, 'specialist', 'security', 'running', '2026-01-01T10:05:00')"
    )
    conn.execute(
        "INSERT INTO session_state VALUES (102, 10, 'specialist', 'perf', 'failed', '2026-01-01T10:10:00')"
    )

    # Messages for session 10
    conn.execute(
        "INSERT INTO messages VALUES (1, 10, 'Hello', 'user', '2026-01-01T10:00:01')"
    )
    conn.execute(
        "INSERT INTO messages VALUES (2, 10, 'World', 'assistant', '2026-01-01T10:00:02')"
    )
    conn.execute(
        "INSERT INTO messages VALUES (3, 10, 'Done', 'user', '2026-01-01T10:00:03')"
    )

    # Findings for session 10 (tied to session_state row 101)
    conn.execute(
        "INSERT INTO findings VALUES (1, 101, 'SQL injection', 'high', '2026-01-01T10:06:00')"
    )

    # Specialist assignments for session 10
    conn.execute(
        "INSERT INTO specialist_assignments VALUES (1, 10, 'security-specialist', 1)"
    )
    conn.execute(
        "INSERT INTO specialist_assignments VALUES (2, 10, 'performance-specialist', 2)"
    )

    conn.commit()
    return conn


@pytest.fixture
def mem_conn():
    conn = make_conn()
    yield conn
    conn.close()


@pytest.fixture
def app(mem_conn):
    """Flask test app with db.connect patched to return the shared in-memory connection."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with patch("dashboard.db.connect", return_value=mem_conn):
        with flask_app.test_client() as client:
            with flask_app.app_context():
                yield flask_app, client, mem_conn


# ---------------------------------------------------------------------------
# db.py tests
# ---------------------------------------------------------------------------


class TestDbConnect:
    def test_returns_connection_with_row_factory(self, tmp_path):
        db_file = tmp_path / "test.db"
        conn = db.connect(str(db_file))
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_connect_default_path_uses_env(self, monkeypatch, tmp_path):
        db_file = tmp_path / "env.db"
        monkeypatch.setenv("DEVTEAM_DB", str(db_file))
        path = db.get_db_path()
        assert path == str(db_file)

    def test_get_db_path_defaults_when_env_absent(self, monkeypatch):
        monkeypatch.delenv("DEVTEAM_DB", raising=False)
        path = db.get_db_path()
        assert "dev-team.db" in path


class TestDictFromRow:
    def test_converts_row_to_dict(self, mem_conn):
        row = mem_conn.execute("SELECT id, name FROM projects WHERE id = 2").fetchone()
        result = db.dict_from_row(row)
        assert isinstance(result, dict)
        assert result["id"] == 2
        assert result["name"] == "Alpha Project"

    def test_returns_none_for_none_input(self):
        assert db.dict_from_row(None) is None


# ---------------------------------------------------------------------------
# models.py tests
# ---------------------------------------------------------------------------


class TestListProjects:
    def test_returns_all_projects_sorted_by_name(self, mem_conn):
        projects = models.list_projects(mem_conn)
        assert len(projects) == 2
        assert projects[0]["name"] == "Alpha Project"
        assert projects[1]["name"] == "Zeta Project"

    def test_returns_dicts(self, mem_conn):
        projects = models.list_projects(mem_conn)
        for p in projects:
            assert isinstance(p, dict)
            assert "id" in p
            assert "name" in p


class TestListSessions:
    def test_returns_all_sessions_with_computed_counts(self, mem_conn):
        sessions = models.list_sessions(mem_conn)
        assert len(sessions) == 2
        session10 = next(s for s in sessions if s["id"] == 10)
        assert session10["agent_total"] == 3
        assert session10["agents_done"] == 1
        assert session10["agents_active"] == 1
        assert session10["agents_failed"] == 1

    def test_includes_project_name(self, mem_conn):
        sessions = models.list_sessions(mem_conn)
        session10 = next(s for s in sessions if s["id"] == 10)
        assert session10["project_name"] == "Zeta Project"

    def test_filters_by_project_id(self, mem_conn):
        sessions = models.list_sessions(mem_conn, project_id=1)
        assert len(sessions) == 1
        assert sessions[0]["id"] == 10

    def test_filters_by_workflow(self, mem_conn):
        sessions = models.list_sessions(mem_conn, workflow="analysis")
        assert len(sessions) == 1
        assert sessions[0]["id"] == 20

    def test_filters_by_status(self, mem_conn):
        sessions = models.list_sessions(mem_conn, status="completed")
        assert len(sessions) == 1
        assert sessions[0]["id"] == 20

    def test_no_results_when_filter_matches_nothing(self, mem_conn):
        sessions = models.list_sessions(mem_conn, status="pending")
        assert sessions == []


class TestGetSession:
    def test_returns_session_with_agents_findings_assignments(self, mem_conn):
        result = models.get_session(mem_conn, 10)
        assert result is not None
        assert result["id"] == 10
        assert result["project_name"] == "Zeta Project"
        assert len(result["agents"]) == 3
        assert len(result["findings"]) == 1
        assert len(result["specialist_assignments"]) == 2

    def test_findings_include_agent_info(self, mem_conn):
        result = models.get_session(mem_conn, 10)
        finding = result["findings"][0]
        assert finding["title"] == "SQL injection"
        assert finding["agent_type"] == "specialist"
        assert finding["agent_specialist"] == "security"

    def test_returns_none_for_nonexistent_id(self, mem_conn):
        result = models.get_session(mem_conn, 9999)
        assert result is None


class TestListMessages:
    def test_returns_messages_ordered_by_id(self, mem_conn):
        messages = models.list_messages(mem_conn, session_id=10)
        assert len(messages) == 3
        ids = [m["id"] for m in messages]
        assert ids == sorted(ids)

    def test_respects_since_id(self, mem_conn):
        messages = models.list_messages(mem_conn, session_id=10, since_id=1)
        assert len(messages) == 2
        assert all(m["id"] > 1 for m in messages)

    def test_since_id_excludes_all_when_high(self, mem_conn):
        messages = models.list_messages(mem_conn, session_id=10, since_id=100)
        assert messages == []

    def test_returns_empty_for_unknown_session(self, mem_conn):
        messages = models.list_messages(mem_conn, session_id=9999)
        assert messages == []


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_returns_ok(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


class TestProjectsEndpoint:
    def test_returns_project_list(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        names = [p["name"] for p in data]
        assert names == ["Alpha Project", "Zeta Project"]


class TestWorkflowsEndpoint:
    def test_returns_session_list(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_filter_by_project_id(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows?project_id=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["id"] == 10

    def test_filter_by_workflow(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows?workflow=discovery")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["workflow"] == "discovery"

    def test_filter_by_status(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows?status=completed")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    def test_returns_computed_agent_counts(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows")
        data = resp.get_json()
        session10 = next(s for s in data if s["id"] == 10)
        assert session10["agent_total"] == 3


class TestWorkflowDetailEndpoint:
    def test_returns_session_detail(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows/10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == 10
        assert "agents" in data
        assert "findings" in data
        assert "specialist_assignments" in data

    def test_returns_404_for_missing_session(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows/9999")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"] == "not found"


class TestMessagesEndpoint:
    def test_returns_messages_for_session(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows/10/messages")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 3

    def test_since_param_filters_messages(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows/10/messages?since=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        assert all(m["id"] > 1 for m in data)

    def test_returns_empty_list_for_unknown_session(self, app):
        _, client, _ = app
        resp = client.get("/api/v1/workflows/9999/messages")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []
