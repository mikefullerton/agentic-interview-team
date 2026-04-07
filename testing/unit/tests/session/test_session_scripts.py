"""
Tests for session-related scripts in plugins/dev-team/scripts/.

Covers:
  - load_config.py
  - version_check.py
  - resume_session.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[4] / "plugins" / "dev-team" / "scripts"
LOAD_CONFIG = str(SCRIPTS_DIR / "load_config.py")
VERSION_CHECK = str(SCRIPTS_DIR / "version_check.py")
RESUME_SESSION = str(SCRIPTS_DIR / "resume_session.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_script(script, args, env=None):
    """Run a script via subprocess and return CompletedProcess."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, script] + args,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# load_config.py tests
# ---------------------------------------------------------------------------

class TestLoadConfig:

    def test_valid_config(self, tmp_path):
        """Valid config with all required fields is echoed as JSON to stdout."""
        config = {
            "workspace_repo": "/repos/workspace",
            "cookbook_repo": "/repos/cookbook",
            "user_name": "alice",
        }
        config_file = tmp_path / "config.json"
        write_json(config_file, config)

        result = run_script(LOAD_CONFIG, ["--config", str(config_file)])

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["workspace_repo"] == "/repos/workspace"
        assert parsed["cookbook_repo"] == "/repos/cookbook"
        assert parsed["user_name"] == "alice"

    def test_missing_config_file(self, tmp_path):
        """Non-existent config path exits with code 1.

        HOME is overridden to an empty temp dir so the migration fallback
        (from ~/.agentic-interviewer/config.json) cannot trigger.
        """
        missing = tmp_path / "does_not_exist.json"
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()

        result = run_script(
            LOAD_CONFIG,
            ["--config", str(missing)],
            env={"HOME": str(fake_home)},
        )

        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "Config" in result.stderr

    def test_missing_required_field(self, tmp_path):
        """Config missing workspace_repo exits with code 1."""
        config = {
            "cookbook_repo": "/repos/cookbook",
            "user_name": "alice",
            # workspace_repo intentionally omitted
        }
        config_file = tmp_path / "config.json"
        write_json(config_file, config)

        result = run_script(LOAD_CONFIG, ["--config", str(config_file)])

        assert result.returncode == 1
        assert (
            "workspace_repo" in result.stderr
            or "required" in result.stderr.lower()
            or "missing" in result.stderr.lower()
        )

    def test_malformed_json(self, tmp_path):
        """Config file with invalid JSON exits with code 1."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("{not valid json}")

        result = run_script(LOAD_CONFIG, ["--config", str(config_file)])

        assert result.returncode == 1


# ---------------------------------------------------------------------------
# version_check.py tests
# ---------------------------------------------------------------------------

SKILL_MD_TEMPLATE = """\
---
name: test-skill
version: {version}
---

# Test Skill
"""

SKILL_MD_NO_VERSION = """\
---
name: test-skill
---

# Test Skill
"""


class TestVersionCheck:

    def _make_skill_dir(self, tmp_path, content):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def test_matching_versions_no_output(self, tmp_path):
        """When running version matches installed version, no stderr and exit 0."""
        skill_dir = self._make_skill_dir(tmp_path, SKILL_MD_TEMPLATE.format(version="1.0.0"))

        result = run_script(VERSION_CHECK, [str(skill_dir), "1.0.0"])

        assert result.returncode == 0
        assert result.stderr.strip() == ""

    def test_mismatched_versions_warns(self, tmp_path):
        """When running version differs from installed, stderr contains a warning with both versions."""
        skill_dir = self._make_skill_dir(tmp_path, SKILL_MD_TEMPLATE.format(version="1.0.0"))

        result = run_script(VERSION_CHECK, [str(skill_dir), "0.9.0"])

        assert result.returncode == 0
        assert "Warning" in result.stderr or "warning" in result.stderr.lower()
        assert "0.9.0" in result.stderr
        assert "1.0.0" in result.stderr

    def test_missing_skill_md_exits_gracefully(self, tmp_path):
        """Directory with no SKILL.md exits 0 without error."""
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()

        result = run_script(VERSION_CHECK, [str(skill_dir), "1.0.0"])

        assert result.returncode == 0

    def test_skill_md_without_version_field(self, tmp_path):
        """SKILL.md present but no version: field exits 0 without error."""
        skill_dir = self._make_skill_dir(tmp_path, SKILL_MD_NO_VERSION)

        result = run_script(VERSION_CHECK, [str(skill_dir), "1.0.0"])

        assert result.returncode == 0


# ---------------------------------------------------------------------------
# resume_session.py tests
#
# resume_session.py resolves arbitrator.sh relative to its own __file__, so
# each test copies the script into a temp scripts dir alongside a fake
# arbitrator.sh that returns controlled JSON. ARBITRATOR_SESSION_BASE is set
# to a temp dir so state file lookups use real paths we control.
# ---------------------------------------------------------------------------

def _make_fake_scripts_dir(tmp_path):
    """Copy resume_session.py into a temp dir so we can place a fake arbitrator next to it."""
    fake_scripts_dir = tmp_path / "scripts"
    fake_scripts_dir.mkdir()
    shutil.copy(RESUME_SESSION, fake_scripts_dir / "resume_session.py")
    return fake_scripts_dir


def _write_fake_arbitrator(scripts_dir, call_counter_path, first_call_response):
    """
    Write a fake arbitrator.sh that returns first_call_response (a JSON-serialisable
    value) on the first invocation and "[]" on all subsequent calls.
    """
    fake_arb = scripts_dir / "arbitrator.sh"
    fake_arb.write_text(f"""\
#!/usr/bin/env python3
import json

counter_file = {str(call_counter_path)!r}
count = int(open(counter_file).read().strip())
open(counter_file, "w").write(str(count + 1))

if count == 0:
    print({json.dumps(json.dumps(first_call_response))})
else:
    print("[]")
""")
    fake_arb.chmod(0o755)
    return fake_arb


class TestResumeSession:

    def test_no_sessions_returns_not_interrupted(self, tmp_path):
        """When arbitrator returns an empty session list, output is {"interrupted": false}."""
        session_base = tmp_path / "sessions"
        session_base.mkdir()

        fake_scripts_dir = _make_fake_scripts_dir(tmp_path)
        fake_arb = fake_scripts_dir / "arbitrator.sh"
        fake_arb.write_text('#!/bin/sh\necho "[]"\n')
        fake_arb.chmod(0o755)

        result = run_script(
            str(fake_scripts_dir / "resume_session.py"),
            ["--playbook", "test-playbook"],
            env={"ARBITRATOR_SESSION_BASE": str(session_base)},
        )

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed == {"interrupted": False}

    def test_interrupted_session_found(self, tmp_path):
        """Session with a non-terminal state is detected and returned with interrupted=true."""
        session_id = "sess-abc-123"
        session_base = tmp_path / "sessions"

        # Create a real state file with a non-terminal state
        state_dir = session_base / session_id / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "001_state.json").write_text(json.dumps({"state": "in_progress"}))

        fake_scripts_dir = _make_fake_scripts_dir(tmp_path)
        call_counter = tmp_path / ".arb_call"
        call_counter.write_text("0")
        session_data = [{"session_id": session_id, "creation_date": "2026-01-01T00:00:00"}]
        _write_fake_arbitrator(fake_scripts_dir, call_counter, session_data)

        result = run_script(
            str(fake_scripts_dir / "resume_session.py"),
            ["--playbook", "test-playbook"],
            env={"ARBITRATOR_SESSION_BASE": str(session_base)},
        )

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["interrupted"] is True
        assert parsed["session_id"] == session_id

    def test_all_sessions_completed_returns_not_interrupted(self, tmp_path):
        """Sessions whose latest state is 'completed' are not flagged as interrupted."""
        session_id = "sess-done-456"
        session_base = tmp_path / "sessions"

        # Create a state file with a terminal state
        state_dir = session_base / session_id / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "001_state.json").write_text(json.dumps({"state": "completed"}))

        fake_scripts_dir = _make_fake_scripts_dir(tmp_path)
        call_counter = tmp_path / ".arb_call"
        call_counter.write_text("0")
        session_data = [{"session_id": session_id, "creation_date": "2026-01-01T00:00:00"}]
        _write_fake_arbitrator(fake_scripts_dir, call_counter, session_data)

        result = run_script(
            str(fake_scripts_dir / "resume_session.py"),
            ["--playbook", "test-playbook"],
            env={"ARBITRATOR_SESSION_BASE": str(session_base)},
        )

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed == {"interrupted": False}

    def test_missing_playbook_arg_exits_1(self):
        """Calling resume_session.py without --playbook exits with code 1."""
        result = run_script(RESUME_SESSION, [])

        assert result.returncode == 1
        assert "playbook" in result.stderr.lower() or "Usage" in result.stderr
