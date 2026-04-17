"""Tests for team-pipeline observer system."""
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
OBSERVERS_DIR = REPO_ROOT / "skills" / "atp" / "scripts" / "observers"
sys.path.insert(0, str(OBSERVERS_DIR))


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("TEAM_PIPELINE_SESSION_BASE", str(tmp_path / "sessions"))
    # Force reimport to pick up env change
    for mod_name in list(sys.modules):
        if "session_paths" in mod_name:
            del sys.modules[mod_name]
    yield tmp_path / "sessions"


def make_event(session_id="test-session", **overrides):
    event = {
        "timestamp": "2026-04-08T12:00:00.000Z",
        "session_id": session_id,
        "agent_id": "agent-1",
        "agent_type": "specialty-team-worker",
        "agent_description": "test worker",
        "status": "completed",
        "duration_ms": 1000,
        "tools_used": ["Read", "Grep"],
        "tool_call_count": 5,
        "summary": "Did some work",
        "transcript_path": "",
    }
    event.update(overrides)
    return event


def test_dispatch_extract_event():
    from dispatch import extract_event
    hook_input = {
        "session_id": "test-123",
        "agent_id": "a1",
        "agent_type": "worker",
        "agent_description": "test",
        "last_assistant_message": "done",
        "agent_transcript_path": "",
    }
    event = extract_event(hook_input)
    assert event["session_id"] == "test-123"
    assert event["status"] == "completed"


def test_dispatch_discover_observers():
    from dispatch import discover_observers
    observers = discover_observers(OBSERVERS_DIR)
    names = [m.__name__ for m in observers]
    assert "stenographer" in names
    assert "oslog" in names
    assert "dispatch" not in names


def test_stenographer_writes_log(isolated_sessions):
    session_dir = isolated_sessions / "test-session"
    session_dir.mkdir(parents=True)

    import importlib
    import session_paths
    importlib.reload(session_paths)
    import stenographer
    importlib.reload(stenographer)

    event = make_event()
    stenographer.observe(event)

    log_file = session_dir / "session.log"
    assert log_file.exists()
    entry = json.loads(log_file.read_text().strip())
    assert entry["sid"] == "test-session"
    assert entry["agent"] == "specialty-team-worker"


def test_oslog_format_message():
    from oslog import format_message
    event = make_event()
    msg = format_message(event)
    assert "team-pipeline" in msg
    assert "specialty-team-worker" in msg
