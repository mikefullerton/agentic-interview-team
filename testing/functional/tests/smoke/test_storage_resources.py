"""Smoke tests for remaining storage-provider resources.

Covers the arbitrator resources not tested in test_storage_provider.py:
gate_option, interpretation, artifact, reference, retry, report, team_result.

And project-storage resources:
milestone, issue, concern, dependency, decision.
"""

import json

from conftest import STORAGE_PROVIDER, run_json, run_ok, run_script


# ---------------------------------------------------------------------------
# Helpers — create prerequisite objects
# ---------------------------------------------------------------------------

def make_session():
    return run_json(STORAGE_PROVIDER, [
        "session", "create",
        "--playbook", "smoke",
        "--team-lead", "tl",
        "--user", "u",
        "--machine", "m",
    ])["session_id"]


def make_result(session_id, specialist="security"):
    return run_json(STORAGE_PROVIDER, [
        "result", "create",
        "--session", session_id,
        "--specialist", specialist,
    ])["result_id"]


def make_finding(session_id, result_id, specialist="security"):
    return run_json(STORAGE_PROVIDER, [
        "finding", "create",
        "--session", session_id,
        "--result", result_id,
        "--specialist", specialist,
        "--category", "auth",
        "--title", "Test finding",
        "--detail", "Detail text",
        "--severity", "info",
    ])


def make_message(session_id):
    return run_json(STORAGE_PROVIDER, [
        "message", "send",
        "--session", session_id,
        "--type", "question",
        "--changed-by", "specialist",
        "--content", "Test message",
    ])


def make_state(session_id, changed_by="team-lead"):
    return run_json(STORAGE_PROVIDER, [
        "state", "append",
        "--session", session_id,
        "--state", "in_progress",
        "--changed-by", changed_by,
    ])


def make_project(project_path):
    project_path.mkdir(parents=True, exist_ok=True)
    run_json(STORAGE_PROVIDER, [
        "project", "init",
        "--name", "Smoke Resource Test",
        "--description", "For resource smoke tests",
        "--path", str(project_path),
    ])
    return str(project_path)


# ---------------------------------------------------------------------------
# Gate Option
# ---------------------------------------------------------------------------

class TestGateOption:
    def test_add_and_list(self):
        sid = make_session()
        msg = make_message(sid)
        msg_id = msg["id"]

        run_json(STORAGE_PROVIDER, [
            "gate-option", "add",
            "--message", msg_id,
            "--option-text", "Approve",
            "--is-default", "true",
            "--sort-order", "1",
        ])
        run_json(STORAGE_PROVIDER, [
            "gate-option", "add",
            "--message", msg_id,
            "--option-text", "Reject",
            "--is-default", "false",
            "--sort-order", "2",
        ])

        options = run_json(STORAGE_PROVIDER, [
            "gate-option", "list",
            "--message", msg_id,
        ])
        assert len(options) == 2
        texts = [o["option_text"] for o in options]
        assert "Approve" in texts
        assert "Reject" in texts


# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------

class TestInterpretation:
    def test_create_and_list(self):
        sid = make_session()
        rid = make_result(sid)
        finding = make_finding(sid, rid)
        finding_id = finding.get("id") or finding.get("finding_id")

        run_json(STORAGE_PROVIDER, [
            "interpretation", "create",
            "--session", sid,
            "--finding", finding_id,
            "--specialist", "security",
            "--interpretation", "This is a good practice",
        ])

        interps = run_json(STORAGE_PROVIDER, [
            "interpretation", "list",
            "--finding", finding_id,
        ])
        assert len(interps) == 1
        assert "good practice" in interps[0]["interpretation"]


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------

class TestArtifact:
    def test_create_and_list(self):
        sid = make_session()

        created = run_json(STORAGE_PROVIDER, [
            "artifact", "create",
            "--session", sid,
            "--artifact", "/tmp/test-artifact.md",
            "--description", "Test artifact",
        ])
        assert "id" in created or "artifact_id" in created

        artifacts = run_json(STORAGE_PROVIDER, [
            "artifact", "list",
            "--session", sid,
        ])
        assert len(artifacts) >= 1

    def test_link_state(self):
        sid = make_session()
        state = make_state(sid)
        state_id = state.get("id") or state.get("state_id")

        created = run_json(STORAGE_PROVIDER, [
            "artifact", "create",
            "--session", sid,
            "--artifact", "/tmp/linked-artifact.md",
        ])
        artifact_id = created.get("id") or created.get("artifact_id")

        run_json(STORAGE_PROVIDER, [
            "artifact", "link-state",
            "--artifact", artifact_id,
            "--state", state_id,
        ])


# ---------------------------------------------------------------------------
# Reference
# ---------------------------------------------------------------------------

class TestReference:
    def test_create_and_list(self):
        sid = make_session()
        rid = make_result(sid)

        run_json(STORAGE_PROVIDER, [
            "reference", "create",
            "--result", rid,
            "--path", "/docs/auth-guide.md",
            "--type", "documentation",
        ])

        refs = run_json(STORAGE_PROVIDER, [
            "reference", "list",
            "--result", rid,
        ])
        assert len(refs) == 1
        assert refs[0]["path"] == "/docs/auth-guide.md"
        assert refs[0]["type"] == "documentation"


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

class TestRetry:
    def test_create_and_list(self):
        sid = make_session()
        state = make_state(sid)
        state_id = state.get("id") or state.get("state_id")

        run_json(STORAGE_PROVIDER, [
            "retry", "create",
            "--session", sid,
            "--state", state_id,
            "--reason", "Verifier found issues",
        ])

        retries = run_json(STORAGE_PROVIDER, [
            "retry", "list",
            "--session", sid,
        ])
        assert len(retries) == 1
        assert "Verifier found issues" in retries[0]["reason"]


# ---------------------------------------------------------------------------
# Team Result
# ---------------------------------------------------------------------------

class TestTeamResult:
    def test_create_get_list_update(self):
        sid = make_session()
        rid = make_result(sid, specialist="testing-qa")

        run_json(STORAGE_PROVIDER, [
            "team-result", "create",
            "--session", sid,
            "--result", rid,
            "--specialist", "testing-qa",
            "--team", "unit-test-patterns",
        ])

        got = run_json(STORAGE_PROVIDER, [
            "team-result", "get",
            "--session", sid,
            "--specialist", "testing-qa",
            "--team", "unit-test-patterns",
        ])
        assert got["team_name"] == "unit-test-patterns"

        results = run_json(STORAGE_PROVIDER, [
            "team-result", "list",
            "--session", sid,
        ])
        assert len(results) >= 1

        run_json(STORAGE_PROVIDER, [
            "team-result", "update",
            "--session", sid,
            "--specialist", "testing-qa",
            "--team", "unit-test-patterns",
            "--status", "verified",
            "--iteration", "2",
        ])

        updated = run_json(STORAGE_PROVIDER, [
            "team-result", "get",
            "--session", sid,
            "--specialist", "testing-qa",
            "--team", "unit-test-patterns",
        ])
        assert updated["status"] == "verified"


# ---------------------------------------------------------------------------
# Report (read-only aggregation)
# ---------------------------------------------------------------------------

class TestReport:
    def test_overview(self):
        sid = make_session()
        rid = make_result(sid)
        make_finding(sid, rid)

        overview = run_json(STORAGE_PROVIDER, [
            "report", "overview",
            "--session", sid,
        ])
        assert "session_id" in overview or "session" in overview or isinstance(overview, dict)

    def test_specialist_report(self):
        sid = make_session()
        rid = make_result(sid)
        make_finding(sid, rid)

        report = run_json(STORAGE_PROVIDER, [
            "report", "specialist",
            "--session", sid,
            "--specialist", "security",
        ])
        assert isinstance(report, (dict, list))

    def test_trace(self):
        sid = make_session()
        make_state(sid)
        make_message(sid)

        trace = run_json(STORAGE_PROVIDER, [
            "report", "trace",
            "--session", sid,
        ])
        assert isinstance(trace, (dict, list))


# ---------------------------------------------------------------------------
# Milestone
# ---------------------------------------------------------------------------

class TestMilestone:
    def test_create_get_list_update_delete(self, project_path):
        proj = make_project(project_path)

        created = run_json(STORAGE_PROVIDER, [
            "milestone", "create",
            "--project", proj,
            "--name", "MVP Launch",
            "--description", "First public release",
            "--status", "planned",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "milestone", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["name"] == "MVP Launch"

        milestones = run_json(STORAGE_PROVIDER, [
            "milestone", "list",
            "--project", proj,
        ])
        assert len(milestones) == 1

        run_json(STORAGE_PROVIDER, [
            "milestone", "update",
            "--project", proj,
            "--id", created["id"],
            "--status", "in-progress",
        ])
        updated = run_json(STORAGE_PROVIDER, [
            "milestone", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert updated["status"] == "in-progress"

        run_json(STORAGE_PROVIDER, [
            "milestone", "delete",
            "--project", proj,
            "--id", created["id"],
        ])
        milestones = run_json(STORAGE_PROVIDER, [
            "milestone", "list",
            "--project", proj,
        ])
        assert len(milestones) == 0


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------

class TestIssue:
    def test_create_get_list_update_delete(self, project_path):
        proj = make_project(project_path)

        created = run_json(STORAGE_PROVIDER, [
            "issue", "create",
            "--project", proj,
            "--title", "Login fails on Safari",
            "--description", "Users report blank screen",
            "--severity", "high",
            "--status", "open",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "issue", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["title"] == "Login fails on Safari"
        assert got["severity"] == "high"

        issues = run_json(STORAGE_PROVIDER, [
            "issue", "list",
            "--project", proj,
        ])
        assert len(issues) == 1

        run_json(STORAGE_PROVIDER, [
            "issue", "update",
            "--project", proj,
            "--id", created["id"],
            "--status", "resolved",
        ])
        updated = run_json(STORAGE_PROVIDER, [
            "issue", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert updated["status"] == "resolved"

        run_json(STORAGE_PROVIDER, [
            "issue", "delete",
            "--project", proj,
            "--id", created["id"],
        ])
        issues = run_json(STORAGE_PROVIDER, [
            "issue", "list",
            "--project", proj,
        ])
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Concern
# ---------------------------------------------------------------------------

class TestConcern:
    def test_create_get_list_update_delete(self, project_path):
        proj = make_project(project_path)

        created = run_json(STORAGE_PROVIDER, [
            "concern", "create",
            "--project", proj,
            "--title", "Scalability risk",
            "--description", "Single-server architecture",
            "--raised-by", "architecture",
            "--status", "open",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "concern", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["title"] == "Scalability risk"

        concerns = run_json(STORAGE_PROVIDER, [
            "concern", "list",
            "--project", proj,
        ])
        assert len(concerns) == 1

        run_json(STORAGE_PROVIDER, [
            "concern", "update",
            "--project", proj,
            "--id", created["id"],
            "--status", "mitigated",
        ])
        updated = run_json(STORAGE_PROVIDER, [
            "concern", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert updated["status"] == "mitigated"

        run_json(STORAGE_PROVIDER, [
            "concern", "delete",
            "--project", proj,
            "--id", created["id"],
        ])
        concerns = run_json(STORAGE_PROVIDER, [
            "concern", "list",
            "--project", proj,
        ])
        assert len(concerns) == 0


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

class TestDependency:
    def test_create_get_list_update_delete(self, project_path):
        proj = make_project(project_path)

        created = run_json(STORAGE_PROVIDER, [
            "dependency", "create",
            "--project", proj,
            "--name", "PostgreSQL 16",
            "--description", "Primary database",
            "--type", "infrastructure",
            "--status", "confirmed",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "dependency", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["name"] == "PostgreSQL 16"
        assert got["type"] == "infrastructure"

        deps = run_json(STORAGE_PROVIDER, [
            "dependency", "list",
            "--project", proj,
        ])
        assert len(deps) == 1

        run_json(STORAGE_PROVIDER, [
            "dependency", "update",
            "--project", proj,
            "--id", created["id"],
            "--status", "provisioned",
        ])
        updated = run_json(STORAGE_PROVIDER, [
            "dependency", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert updated["status"] == "provisioned"

        run_json(STORAGE_PROVIDER, [
            "dependency", "delete",
            "--project", proj,
            "--id", created["id"],
        ])
        deps = run_json(STORAGE_PROVIDER, [
            "dependency", "list",
            "--project", proj,
        ])
        assert len(deps) == 0


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

class TestDecision:
    def test_create_get_list_update_delete(self, project_path):
        proj = make_project(project_path)

        created = run_json(STORAGE_PROVIDER, [
            "decision", "create",
            "--project", proj,
            "--title", "Use PostgreSQL over MySQL",
            "--description", "Better JSON support and extensions",
            "--rationale", "JSONB columns, strong ecosystem",
            "--made-by", "architecture",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "decision", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["title"] == "Use PostgreSQL over MySQL"
        assert got["rationale"] == "JSONB columns, strong ecosystem"

        decisions = run_json(STORAGE_PROVIDER, [
            "decision", "list",
            "--project", proj,
        ])
        assert len(decisions) == 1

        run_json(STORAGE_PROVIDER, [
            "decision", "update",
            "--project", proj,
            "--id", created["id"],
            "--rationale", "Updated: JSONB + PostGIS for geo data",
        ])
        updated = run_json(STORAGE_PROVIDER, [
            "decision", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert "PostGIS" in updated["rationale"]

        run_json(STORAGE_PROVIDER, [
            "decision", "delete",
            "--project", proj,
            "--id", created["id"],
        ])
        decisions = run_json(STORAGE_PROVIDER, [
            "decision", "list",
            "--project", proj,
        ])
        assert len(decisions) == 0
