"""Smoke tests for the observer system.

Verifies observer discovery, event extraction, dispatch isolation,
and that the real observers (stenographer, oslog) can be loaded.
"""

import json
import sys
import types
from pathlib import Path

import pytest

from conftest import PLUGIN_ROOT

OBSERVERS_DIR = PLUGIN_ROOT / "scripts" / "observers"

# Import dispatch module directly for unit-level smoke checks
sys.path.insert(0, str(OBSERVERS_DIR.parent))
sys.path.insert(0, str(OBSERVERS_DIR))

from observers.dispatch import discover_observers, extract_event, run_observers


# ---------------------------------------------------------------------------
# Event extraction
# ---------------------------------------------------------------------------

class TestExtractEvent:
    def test_minimal_hook_input(self):
        hook_input = {
            "session_id": "sess-001",
            "agent_id": "agent-1",
            "agent_type": "specialist",
            "agent_description": "test agent",
        }
        event = extract_event(hook_input)
        assert event["session_id"] == "sess-001"
        assert event["agent_type"] == "specialist"
        assert event["status"] == "completed"
        assert isinstance(event["tools_used"], list)
        assert isinstance(event["tool_call_count"], int)

    def test_long_message_is_truncated(self):
        hook_input = {
            "last_assistant_message": "x" * 300,
        }
        event = extract_event(hook_input)
        assert len(event["summary"]) <= 200

    def test_transcript_parsing(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"type": "tool_use", "name": "Read"}),
            json.dumps({"type": "tool_use", "name": "Write"}),
            json.dumps({"type": "tool_use", "name": "Read"}),
            json.dumps({"type": "text", "content": "hello"}),
        ]
        transcript.write_text("\n".join(lines))

        hook_input = {"agent_transcript_path": str(transcript)}
        event = extract_event(hook_input)
        assert event["tool_call_count"] == 3
        assert sorted(event["tools_used"]) == ["Read", "Write"]


# ---------------------------------------------------------------------------
# Observer discovery
# ---------------------------------------------------------------------------

class TestDiscoverObservers:
    def test_discovers_real_observers(self):
        observers = discover_observers(OBSERVERS_DIR)
        assert len(observers) >= 2, (
            f"Expected at least 2 observers (stenographer, oslog), "
            f"found {len(observers)}: {[m.__name__ for m in observers]}"
        )

    def test_all_discovered_have_observe_function(self):
        observers = discover_observers(OBSERVERS_DIR)
        for obs in observers:
            assert hasattr(obs, "observe"), (
                f"Observer {obs.__name__} missing observe() function"
            )

    def test_skips_dispatch_and_private_files(self, tmp_path):
        """dispatch.py and _*.py files are not loaded as observers."""
        (tmp_path / "dispatch.py").write_text("def observe(e): pass")
        (tmp_path / "_private.py").write_text("def observe(e): pass")
        (tmp_path / "real_observer.py").write_text("def observe(e): pass")

        observers = discover_observers(tmp_path)
        names = [m.__name__ for m in observers]
        assert "dispatch" not in names
        assert "_private" not in names
        assert "real_observer" in names


# ---------------------------------------------------------------------------
# Observer dispatch isolation
# ---------------------------------------------------------------------------

class TestRunObservers:
    def test_calls_all_observers(self):
        calls = []

        def make_observer(name):
            mod = types.ModuleType(name)
            mod.observe = lambda e: calls.append(name)
            return mod

        observers = [make_observer("obs_a"), make_observer("obs_b")]
        run_observers(observers, {"test": True})
        assert calls == ["obs_a", "obs_b"]

    def test_failing_observer_does_not_block_others(self):
        calls = []

        good = types.ModuleType("good")
        good.observe = lambda e: calls.append("good")

        bad = types.ModuleType("bad")
        bad.observe = lambda e: (_ for _ in ()).throw(RuntimeError("boom"))

        run_observers([bad, good], {"test": True})
        assert "good" in calls


# ---------------------------------------------------------------------------
# Stenographer integration
# ---------------------------------------------------------------------------

class TestStenographerSmoke:
    def test_stenographer_writes_log(self, tmp_path):
        """Stenographer observer writes event to JSONL log file.

        session_paths.py reads ARBITRATOR_SESSION_BASE at import time,
        so we must set the env var before importing the module fresh.
        """
        import importlib
        import importlib.util
        import os

        steno_path = OBSERVERS_DIR / "stenographer.py"
        if not steno_path.exists():
            pytest.skip("stenographer.py not found")

        session_base = tmp_path / "sessions"
        session_dir = session_base / "smoke-test"
        session_dir.mkdir(parents=True)

        old_base = os.environ.get("ARBITRATOR_SESSION_BASE")
        os.environ["ARBITRATOR_SESSION_BASE"] = str(session_base)

        try:
            # Force-reload session_paths so it picks up the new env var
            if "session_paths" in sys.modules:
                del sys.modules["session_paths"]

            # Load stenographer fresh
            spec = importlib.util.spec_from_file_location(
                "stenographer_smoke", steno_path
            )
            steno = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(steno)

            event = {
                "timestamp": "2026-01-01T00:00:00.000Z",
                "session_id": "smoke-test",
                "agent_id": "agent-1",
                "agent_type": "specialist",
                "agent_description": "smoke",
                "status": "completed",
                "duration_ms": 0,
                "tools_used": [],
                "tool_call_count": 0,
                "summary": "test event",
                "transcript_path": "",
            }
            steno.observe(event)

            log_file = session_dir / "session.log"
            assert log_file.exists(), (
                f"Stenographer did not write session.log. "
                f"Contents of {session_base}: {list(session_base.rglob('*'))}"
            )
            content = log_file.read_text()
            assert "smoke-test" in content
        finally:
            if old_base is not None:
                os.environ["ARBITRATOR_SESSION_BASE"] = old_base
            else:
                os.environ.pop("ARBITRATOR_SESSION_BASE", None)
