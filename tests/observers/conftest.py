"""Test fixtures for observer tests."""
import os
import pytest
from pathlib import Path


@pytest.fixture
def tmp_session_dir(tmp_path):
    """Provide a temporary session directory."""
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    return sessions


@pytest.fixture
def sample_event():
    """A normalized event for testing observers."""
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
def sample_transcript_jsonl(tmp_path):
    """Create a mock transcript JSONL file."""
    transcript = tmp_path / "transcript.jsonl"
    import json
    lines = [
        {"type": "tool_use", "name": "Read", "input": {"file_path": "/some/file.py"}},
        {"type": "tool_result", "content": "file contents here"},
        {"type": "assistant", "content": "I'll update the file now."},
        {"type": "tool_use", "name": "Write", "input": {"file_path": "/some/file.py"}},
        {"type": "tool_result", "content": "File written."},
        {"type": "assistant", "content": "Done. Updated the parser.\n\n**Status:** DONE"},
    ]
    transcript.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    return transcript
