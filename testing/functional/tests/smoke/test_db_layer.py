"""Smoke tests for the database layer (plugins/dev-team/scripts/db/).

Covers db_init, db_project, db_run, db_agent, db_message,
db_artifact, db_finding, db_query, and db_cleanup.
All tests use an isolated temp database via DEVTEAM_DB_PATH.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
DB_SCRIPTS = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db"

DB_INIT = str(DB_SCRIPTS / "db_init.py")
DB_PROJECT = str(DB_SCRIPTS / "db_project.py")
DB_RUN = str(DB_SCRIPTS / "db_run.py")
DB_AGENT = str(DB_SCRIPTS / "db_agent.py")
DB_MESSAGE = str(DB_SCRIPTS / "db_message.py")
DB_ARTIFACT = str(DB_SCRIPTS / "db_artifact.py")
DB_FINDING = str(DB_SCRIPTS / "db_finding.py")
DB_QUERY = str(DB_SCRIPTS / "db_query.py")
DB_CLEANUP = str(DB_SCRIPTS / "db_cleanup.py")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Each test gets its own SQLite database."""
    db_path = tmp_path / "test.db"
    os.environ["DEVTEAM_DB_PATH"] = str(db_path)
    yield db_path
    os.environ.pop("DEVTEAM_DB_PATH", None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_db(script, args, env=None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, script] + list(args),
        capture_output=True, text=True, env=merged,
    )


def run_db_ok(script, args, env=None):
    result = run_db(script, args, env=env)
    assert result.returncode == 0, (
        f"Script failed (rc={result.returncode}):\n"
        f"  cmd: {script} {' '.join(args)}\n"
        f"  stderr: {result.stderr}"
    )
    return result.stdout.strip()


def run_db_json(script, args, env=None):
    stdout = run_db_ok(script, args, env=env)
    return json.loads(stdout)


def create_project(name="Smoke Project", path="/tmp/smoke"):
    return run_db_json(DB_PROJECT, ["--name", name, "--path", path])


def create_session(project_id, workflow="interview"):
    return run_db_json(DB_RUN, [
        "start", "--project", str(project_id), "--workflow", workflow,
    ])


# ---------------------------------------------------------------------------
# db_init.py
# ---------------------------------------------------------------------------

class TestDbInit:
    def test_creates_database(self, isolated_db):
        stdout = run_db_ok(DB_INIT, [])
        assert str(isolated_db) in stdout

    def test_idempotent(self, isolated_db):
        run_db_ok(DB_INIT, [])
        run_db_ok(DB_INIT, [])
        # No error on second run
        assert isolated_db.exists()


# ---------------------------------------------------------------------------
# db_project.py
# ---------------------------------------------------------------------------

class TestDbProject:
    def test_create_and_get(self):
        result = create_project("Test App", "/repos/test-app")
        assert result["id"] > 0

        got = run_db_json(DB_PROJECT, ["--get", str(result["id"])])
        assert len(got) == 1
        assert got[0]["name"] == "Test App"
        assert got[0]["path"] == "/repos/test-app"

    def test_upsert_same_name(self):
        r1 = create_project("Upsert App", "/old/path")
        r2 = run_db_json(DB_PROJECT, [
            "--name", "Upsert App", "--path", "/new/path",
        ])
        assert r1["id"] == r2["id"]

        got = run_db_json(DB_PROJECT, ["--get", str(r1["id"])])
        assert got[0]["path"] == "/new/path"

    def test_list_projects(self):
        create_project("App A", "/a")
        create_project("App B", "/b")

        projects = run_db_json(DB_PROJECT, ["--list"])
        assert len(projects) >= 2
        names = [p["name"] for p in projects]
        assert "App A" in names
        assert "App B" in names


# ---------------------------------------------------------------------------
# db_run.py
# ---------------------------------------------------------------------------

class TestDbRun:
    def test_start_and_get(self):
        proj = create_project()
        session = create_session(proj["id"])
        assert session["id"] > 0

        got = run_db_json(DB_RUN, ["--get", str(session["id"])])
        assert len(got) == 1
        assert got[0]["status"] == "running"
        assert got[0]["workflow"] == "interview"

    def test_complete_session(self):
        proj = create_project()
        session = create_session(proj["id"])

        result = run_db_json(DB_RUN, [
            "complete", "--id", str(session["id"]), "--status", "completed",
        ])
        assert result["status"] == "completed"

        got = run_db_json(DB_RUN, ["--get", str(session["id"])])
        assert got[0]["status"] == "completed"
        assert got[0]["completed"] is not None

    def test_latest(self):
        proj = create_project()
        s1 = create_session(proj["id"], "interview")
        s2 = create_session(proj["id"], "interview")

        latest = run_db_json(DB_RUN, [
            "--latest", "--project", str(proj["id"]), "--workflow", "interview",
        ])
        assert len(latest) == 1
        # Both created in same second, so latest by id is acceptable
        assert latest[0]["id"] in (s1["id"], s2["id"])


# ---------------------------------------------------------------------------
# db_agent.py
# ---------------------------------------------------------------------------

class TestDbAgent:
    def test_start_and_complete(self):
        proj = create_project()
        session = create_session(proj["id"])

        state = run_db_json(DB_AGENT, [
            "start",
            "--run", str(session["id"]),
            "--agent", "specialist",
            "--specialist", "security",
        ])
        assert state["id"] > 0

        result = run_db_json(DB_AGENT, [
            "complete",
            "--id", str(state["id"]),
            "--status", "completed",
            "--output-path", "/tmp/output.md",
        ])
        assert result["status"] == "completed"

    def test_start_without_specialist(self):
        proj = create_project()
        session = create_session(proj["id"])

        state = run_db_json(DB_AGENT, [
            "start",
            "--run", str(session["id"]),
            "--agent", "coordinator",
        ])
        assert state["id"] > 0


# ---------------------------------------------------------------------------
# db_message.py
# ---------------------------------------------------------------------------

class TestDbMessage:
    def test_create_message(self):
        proj = create_project()
        session = create_session(proj["id"])

        msg = run_db_json(DB_MESSAGE, [
            "--run", str(session["id"]),
            "--message", "Starting specialist analysis",
            "--agent-type", "specialist",
            "--specialist", "security",
        ])
        assert msg["id"] > 0

    def test_create_message_with_all_fields(self):
        proj = create_project()
        session = create_session(proj["id"])
        state = run_db_json(DB_AGENT, [
            "start", "--run", str(session["id"]), "--agent", "specialist",
        ])

        msg = run_db_json(DB_MESSAGE, [
            "--run", str(session["id"]),
            "--session-state", str(state["id"]),
            "--agent-type", "specialist",
            "--specialist", "security",
            "--persona", "Alex the Security Expert",
            "--message", "Analyzing authentication flow",
        ])
        assert msg["id"] > 0


# ---------------------------------------------------------------------------
# db_artifact.py
# ---------------------------------------------------------------------------

class TestDbArtifact:
    def test_write_and_get(self, tmp_path):
        proj = create_project()
        artifact_file = tmp_path / "test-artifact.md"
        artifact_file.write_text("---\ntitle: Test Doc\n---\n\n# Hello World\n")

        written = run_db_json(DB_ARTIFACT, [
            "write",
            "--project", str(proj["id"]),
            "--path", str(artifact_file),
            "--category", "documentation",
        ])
        assert "id" in written

        got = run_db_json(DB_ARTIFACT, ["get", "--id", str(written["id"])])
        assert len(got) == 1
        assert got[0]["title"] == "Test Doc"
        assert got[0]["category"] == "documentation"

    def test_version_increment(self, tmp_path):
        proj = create_project()
        artifact_file = tmp_path / "versioned.md"
        artifact_file.write_text("v1 content")

        w1 = run_db_json(DB_ARTIFACT, [
            "write", "--project", str(proj["id"]),
            "--path", str(artifact_file), "--category", "code",
        ])

        artifact_file.write_text("v2 content")
        w2 = run_db_json(DB_ARTIFACT, [
            "write", "--project", str(proj["id"]),
            "--path", str(artifact_file), "--category", "code",
        ])
        assert w2["version"] == 2
        assert w1["id"] == w2["id"]

    def test_search(self, tmp_path):
        proj = create_project()
        for name, cat in [("a.md", "code"), ("b.md", "test"), ("c.md", "code")]:
            f = tmp_path / name
            f.write_text(f"Content of {name}")
            run_db_ok(DB_ARTIFACT, [
                "write", "--project", str(proj["id"]),
                "--path", str(f), "--category", cat,
            ])

        all_results = run_db_json(DB_ARTIFACT, [
            "search", "--project", str(proj["id"]),
        ])
        assert len(all_results) == 3

        code_only = run_db_json(DB_ARTIFACT, [
            "search", "--project", str(proj["id"]), "--category", "code",
        ])
        assert len(code_only) == 2

    def test_text_search(self, tmp_path):
        proj = create_project()
        f = tmp_path / "searchable.md"
        f.write_text("This contains a unique_keyword_xyz for testing")
        run_db_ok(DB_ARTIFACT, [
            "write", "--project", str(proj["id"]),
            "--path", str(f), "--category", "doc",
        ])

        results = run_db_json(DB_ARTIFACT, [
            "search", "--project", str(proj["id"]), "--text", "unique_keyword_xyz",
        ])
        assert len(results) == 1


# ---------------------------------------------------------------------------
# db_finding.py
# ---------------------------------------------------------------------------

class TestDbFinding:
    def test_create_and_list(self):
        proj = create_project()

        created = run_db_json(DB_FINDING, [
            "--project", str(proj["id"]),
            "--type", "security",
            "--severity", "high",
            "--description", "SQL injection risk in login form",
        ])
        assert created["id"] > 0

        findings = run_db_json(DB_FINDING, [
            "--list", "--project", str(proj["id"]),
        ])
        assert len(findings) == 1
        assert findings[0]["description"] == "SQL injection risk in login form"
        assert findings[0]["status"] == "open"

    def test_update_status(self):
        proj = create_project()
        created = run_db_json(DB_FINDING, [
            "--project", str(proj["id"]),
            "--type", "bug",
            "--description", "Off-by-one error",
        ])

        updated = run_db_json(DB_FINDING, [
            "update", "--id", str(created["id"]), "--status", "fixed",
        ])
        assert updated["status"] == "fixed"

    def test_list_with_filters(self):
        proj = create_project()
        run_db_ok(DB_FINDING, [
            "--project", str(proj["id"]),
            "--type", "security", "--description", "XSS",
        ])
        run_db_ok(DB_FINDING, [
            "--project", str(proj["id"]),
            "--type", "bug", "--description", "Crash on load",
        ])

        security_only = run_db_json(DB_FINDING, [
            "--list", "--project", str(proj["id"]), "--type", "security",
        ])
        assert len(security_only) == 1

    def test_create_with_session_state(self):
        proj = create_project()
        session = create_session(proj["id"])
        state = run_db_json(DB_AGENT, [
            "start", "--run", str(session["id"]), "--agent", "specialist",
        ])

        created = run_db_json(DB_FINDING, [
            "--session-state", str(state["id"]),
            "--project", str(proj["id"]),
            "--type", "quality",
            "--description", "Missing error handling",
        ])
        assert created["id"] > 0


# ---------------------------------------------------------------------------
# db_query.py
# ---------------------------------------------------------------------------

class TestDbQuery:
    def test_json_output(self):
        create_project("Query Test", "/q")

        result = run_db_json(DB_QUERY, [
            "SELECT name, path FROM projects WHERE name='Query Test'",
        ])
        assert len(result) == 1
        assert result[0]["name"] == "Query Test"

    def test_table_output(self):
        create_project("Table Test", "/t")

        stdout = run_db_ok(DB_QUERY, [
            "--table", "SELECT name, path FROM projects WHERE name='Table Test'",
        ])
        lines = stdout.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "name" in lines[0]
        assert "Table Test" in lines[1]

    def test_empty_result(self):
        run_db_ok(DB_INIT, [])
        result = run_db_json(DB_QUERY, [
            "SELECT * FROM projects WHERE name='nonexistent'",
        ])
        assert result == []


# ---------------------------------------------------------------------------
# db_cleanup.py
# ---------------------------------------------------------------------------

class TestDbCleanup:
    def test_no_stale_sessions(self):
        run_db_ok(DB_INIT, [])
        result = run_db_json(DB_CLEANUP, ["--older-than", "90d"])
        assert result["deleted"]["sessions"] == 0

    def test_recent_sessions_not_deleted(self):
        proj = create_project()
        create_session(proj["id"])

        result = run_db_json(DB_CLEANUP, ["--older-than", "1d"])
        assert result["deleted"]["sessions"] == 0

    def test_cascading_delete(self, isolated_db):
        """Insert old data directly via SQLite, verify cleanup cascades."""
        import sqlite3

        proj = create_project()
        run_db_ok(DB_INIT, [])

        # Insert old session and message directly (db_query doesn't commit writes)
        conn = sqlite3.connect(str(isolated_db))
        conn.execute("PRAGMA foreign_keys=ON")
        cur = conn.execute(
            "INSERT INTO sessions (project_id, workflow, started) "
            "VALUES (?, 'old-workflow', datetime('now', '-100 days'))",
            (proj["id"],),
        )
        old_sid = cur.lastrowid
        conn.execute(
            "INSERT INTO messages (session_id, message) VALUES (?, 'old message')",
            (old_sid,),
        )
        conn.commit()
        conn.close()

        # Clean up anything older than 90 days
        result = run_db_json(DB_CLEANUP, ["--older-than", "90d"])
        assert result["deleted"]["sessions"] == 1
        assert result["deleted"]["messages"] == 1

    def test_missing_flag_exits_nonzero(self):
        run_db_ok(DB_INIT, [])
        result = run_db(DB_CLEANUP, [])
        assert result.returncode != 0

    def test_invalid_duration_exits_nonzero(self):
        run_db_ok(DB_INIT, [])
        result = run_db(DB_CLEANUP, ["--older-than", "abc"])
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Full db pipeline
# ---------------------------------------------------------------------------

class TestDbPipeline:
    """End-to-end: project → session → agent states → messages → findings → artifacts."""

    def test_full_workflow(self, tmp_path):
        # 1. Create project
        proj = create_project("Pipeline App", "/repos/pipeline")

        # 2. Start session
        session = create_session(proj["id"], "analysis")

        # 3. Start agent
        state = run_db_json(DB_AGENT, [
            "start",
            "--run", str(session["id"]),
            "--agent", "specialist",
            "--specialist", "security",
        ])

        # 4. Log messages
        run_db_json(DB_MESSAGE, [
            "--run", str(session["id"]),
            "--session-state", str(state["id"]),
            "--agent-type", "specialist",
            "--specialist", "security",
            "--message", "Analyzing authentication patterns",
        ])

        # 5. Record finding
        finding = run_db_json(DB_FINDING, [
            "--session-state", str(state["id"]),
            "--project", str(proj["id"]),
            "--type", "security",
            "--severity", "high",
            "--description", "Missing rate limiting on auth endpoint",
        ])

        # 6. Store artifact
        artifact_file = tmp_path / "report.md"
        artifact_file.write_text("---\ntitle: Security Report\n---\n\n## Findings\n\nRate limiting needed.")
        run_db_json(DB_ARTIFACT, [
            "write",
            "--project", str(proj["id"]),
            "--run", str(session["id"]),
            "--session-state", str(state["id"]),
            "--path", str(artifact_file),
            "--category", "report",
            "--specialist", "security",
        ])

        # 7. Complete agent
        run_db_json(DB_AGENT, [
            "complete",
            "--id", str(state["id"]),
            "--status", "completed",
        ])

        # 8. Complete session
        run_db_json(DB_RUN, [
            "complete", "--id", str(session["id"]), "--status", "completed",
        ])

        # 9. Verify everything is queryable
        projects = run_db_json(DB_PROJECT, ["--list"])
        assert any(p["name"] == "Pipeline App" for p in projects)

        findings = run_db_json(DB_FINDING, [
            "--list", "--project", str(proj["id"]),
        ])
        assert len(findings) == 1

        artifacts = run_db_json(DB_ARTIFACT, [
            "search", "--project", str(proj["id"]),
        ])
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "Security Report"
