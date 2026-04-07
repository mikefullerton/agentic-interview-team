"""Consolidated tests for the observer system.

Covers extract_event() in dispatch.py, stenographer.observe(),
oslog.observe(), and session_paths.get_session_log_path().
"""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

OBSERVERS_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "plugins"
    / "dev-team"
    / "scripts"
    / "observers"
)
sys.path.insert(0, str(OBSERVERS_DIR))


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_event():
    """A fully-populated normalized event."""
    return {
        "timestamp": "2026-04-06T16:02:03.000Z",
        "session_id": "20260406-160200-a1b2",
        "agent_id": "abc123",
        "agent_type": "general-purpose",
        "agent_description": "Implement Task 4",
        "status": "completed",
        "duration_ms": 45000,
        "tools_used": ["Read", "Write", "Bash"],
        "tool_call_count": 16,
        "summary": "Updated run_specialty_teams.py to parse consulting teams.",
        "transcript_path": "/tmp/fake-transcript.jsonl",
    }


@pytest.fixture
def tmp_session_base(tmp_path):
    """Temporary directory that stands in for ARBITRATOR_SESSION_BASE."""
    base = tmp_path / "sessions"
    base.mkdir()
    return base


@pytest.fixture
def transcript_with_tools(tmp_path):
    """JSONL transcript containing two distinct tool_use entries."""
    path = tmp_path / "transcript.jsonl"
    lines = [
        {"type": "tool_use", "name": "Read"},
        {"type": "tool_use", "name": "Write"},
        {"type": "text", "content": "hello"},
    ]
    path.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# extract_event() — unit tests
# ---------------------------------------------------------------------------


class TestExtractEvent:
    """Unit tests for dispatch.extract_event()."""

    def setup_method(self):
        from dispatch import extract_event
        self.extract_event = extract_event

    def test_returns_normalized_event_fields(self, transcript_with_tools):
        hook_input = {
            "session_id": "s-001",
            "agent_id": "ag-001",
            "agent_type": "general-purpose",
            "agent_transcript_path": str(transcript_with_tools),
            "last_assistant_message": "Work complete.",
        }

        event = self.extract_event(hook_input)

        assert event["session_id"] == "s-001"
        assert event["agent_id"] == "ag-001"
        assert event["agent_type"] == "general-purpose"
        assert event["status"] == "completed"
        assert event["summary"] == "Work complete."
        assert isinstance(event["timestamp"], str)
        # tools_used is a sorted list in the returned event
        assert set(event["tools_used"]) == {"Read", "Write"}
        assert event["tool_call_count"] == 2

    def test_empty_transcript_produces_zero_tool_stats(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")

        hook_input = {
            "session_id": "s-002",
            "agent_id": "ag-002",
            "agent_type": "general-purpose",
            "agent_transcript_path": str(path),
            "last_assistant_message": "Done.",
        }

        event = self.extract_event(hook_input)

        assert event["tools_used"] == []
        assert event["tool_call_count"] == 0

    def test_missing_transcript_does_not_crash(self, tmp_path):
        hook_input = {
            "session_id": "s-003",
            "agent_id": "ag-003",
            "agent_type": "general-purpose",
            "agent_transcript_path": str(tmp_path / "nonexistent.jsonl"),
            "last_assistant_message": "Done.",
        }

        event = self.extract_event(hook_input)

        assert event["tools_used"] == []
        assert event["tool_call_count"] == 0
        assert event["status"] == "completed"

    def test_transcript_with_no_tool_use_entries(self, tmp_path):
        path = tmp_path / "no_tools.jsonl"
        lines = [
            {"type": "text", "content": "some assistant text"},
            {"type": "tool_result", "content": "result"},
        ]
        path.write_text("\n".join(json.dumps(l) for l in lines) + "\n")

        hook_input = {
            "session_id": "s-004",
            "agent_id": "ag-004",
            "agent_type": "general-purpose",
            "agent_transcript_path": str(path),
            "last_assistant_message": "Done.",
        }

        event = self.extract_event(hook_input)

        assert event["tool_call_count"] == 0
        assert event["tools_used"] == []

    def test_long_summary_is_truncated_to_200_chars(self):
        long_msg = "x" * 500

        hook_input = {
            "session_id": "s-005",
            "agent_id": "ag-005",
            "agent_type": "general-purpose",
            "agent_transcript_path": "/nonexistent",
            "last_assistant_message": long_msg,
        }

        event = self.extract_event(hook_input)

        assert len(event["summary"]) == 200
        assert event["summary"].endswith("...")


# ---------------------------------------------------------------------------
# stenographer.observe() — unit tests
# ---------------------------------------------------------------------------


class TestStenographer:
    """Unit tests for stenographer.observe()."""

    def _reload_modules(self, session_base: Path):
        """Reload session_paths and stenographer so the env var is picked up."""
        os.environ["ARBITRATOR_SESSION_BASE"] = str(session_base)
        import session_paths
        importlib.reload(session_paths)
        import stenographer
        importlib.reload(stenographer)
        return stenographer

    def teardown_method(self):
        os.environ.pop("ARBITRATOR_SESSION_BASE", None)

    def test_writes_jsonl_entry_to_session_log(self, tmp_session_base, sample_event):
        session_dir = tmp_session_base / sample_event["session_id"]
        session_dir.mkdir()

        steno = self._reload_modules(tmp_session_base)
        steno.observe(sample_event)

        log_path = session_dir / "session.log"
        assert log_path.exists()

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["ts"] == sample_event["timestamp"]
        assert entry["sid"] == sample_event["session_id"]
        assert entry["agent"] == "general-purpose"
        assert entry["desc"] == "Implement Task 4"
        assert entry["status"] == "completed"
        assert entry["duration_ms"] == 45000
        assert entry["tools"] == ["Bash", "Read", "Write"]
        assert entry["calls"] == 16
        assert "summary" in entry

    def test_falls_back_to_observer_log_when_session_missing(
        self, tmp_session_base, sample_event
    ):
        # Do NOT create the session directory — no matching session exists.
        steno = self._reload_modules(tmp_session_base)
        steno.observe(sample_event)

        fallback = tmp_session_base / "_logs" / "observer.log"
        assert fallback.exists()

    def test_truncates_long_summary_in_log_entry(self, tmp_session_base, sample_event):
        session_dir = tmp_session_base / sample_event["session_id"]
        session_dir.mkdir()

        sample_event["summary"] = "y" * 500

        steno = self._reload_modules(tmp_session_base)
        steno.observe(sample_event)

        log_path = session_dir / "session.log"
        entry = json.loads(log_path.read_text().strip())
        assert len(entry["summary"]) <= 200
        assert entry["summary"].endswith("...")


# ---------------------------------------------------------------------------
# oslog.observe() — unit tests
# ---------------------------------------------------------------------------


class TestOslog:
    """Unit tests for oslog.observe()."""

    def setup_method(self):
        import oslog
        self.oslog = oslog

    def test_observe_calls_logger_with_correct_command(self, sample_event):
        with patch("oslog.subprocess.run") as mock_run:
            self.oslog.observe(sample_event)

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd == [
                "logger",
                "-t",
                "dev-team",
                "-p",
                "user.info",
                mock_run.call_args[0][0][-1],
            ]
            assert cmd[0] == "logger"
            assert cmd[1] == "-t"
            assert cmd[2] == "dev-team"
            assert cmd[3] == "-p"
            assert cmd[4] == "user.info"

    def test_message_format_contains_expected_fields(self, sample_event):
        msg = self.oslog.format_message(sample_event)

        assert "[dev-team]" in msg
        assert "general-purpose" in msg
        assert "Implement Task 4" in msg
        assert "completed" in msg
        # duration_ms=45000 → 45s
        assert "45s" in msg
        assert "16 calls" in msg

    def test_observe_silently_handles_missing_logger(self, sample_event):
        with patch("oslog.subprocess.run", side_effect=FileNotFoundError):
            # Must not raise
            self.oslog.observe(sample_event)

    def test_observe_silently_handles_timeout(self, sample_event):
        with patch(
            "oslog.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="logger", timeout=5),
        ):
            # Must not raise
            self.oslog.observe(sample_event)


# ---------------------------------------------------------------------------
# session_paths.get_session_log_path() — unit tests
# ---------------------------------------------------------------------------


class TestSessionPaths:
    """Unit tests for session_paths.get_session_log_path()."""

    def _reload(self, base: Path):
        os.environ["ARBITRATOR_SESSION_BASE"] = str(base)
        import session_paths
        importlib.reload(session_paths)
        return session_paths

    def teardown_method(self):
        os.environ.pop("ARBITRATOR_SESSION_BASE", None)

    def test_returns_session_log_when_session_dir_exists(self, tmp_session_base):
        session_id = "20260406-160200-a1b2"
        session_dir = tmp_session_base / session_id
        session_dir.mkdir()

        sp = self._reload(tmp_session_base)
        result = sp.get_session_log_path(session_id)

        assert result == session_dir / "session.log"

    def test_returns_fallback_log_when_session_dir_missing(self, tmp_session_base):
        session_id = "nonexistent-session"

        sp = self._reload(tmp_session_base)
        result = sp.get_session_log_path(session_id)

        assert result == tmp_session_base / "_logs" / "observer.log"
