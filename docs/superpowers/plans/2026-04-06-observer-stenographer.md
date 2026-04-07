# Observer System + Stenographer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an observer system that captures subagent activity via a `SubagentStop` hook and dispatches normalized events to auto-discovered observer modules, with two built-in observers: stenographer (session.log JSONL) and oslog (system log).

**Architecture:** Single `SubagentStop` hook calls `dispatch.py`, which reads the subagent transcript JSONL, extracts a normalized event, and calls `observe(event)` on every `.py` file in `scripts/observers/` (excluding `dispatch.py` and `_`-prefixed files). Each observer does one thing with the event.

**Tech Stack:** Python 3, pytest, Claude Code hooks (settings.json), POSIX `logger` CLI.

---

## File Structure

### New files

```
plugins/dev-team/
  scripts/
    observers/
      _lib.py                # Shared utilities (session log path resolution)
      dispatch.py            # Hook entry point — reads stdin, extracts event, calls observers
      stenographer.py        # Writes session.log JSONL
      oslog.py               # Writes to system log via logger CLI

.claude/
  settings.json              # SubagentStop hook configuration

tests/
  observers/
    conftest.py              # Test fixtures (mock events, tmp dirs)
    test_dispatch.py         # Event extraction + auto-discovery tests
    test_stenographer.py     # Log entry format + append tests
    test_oslog.py            # Message formatting tests
```

### Modified files

```
docs/
  architecture.md            # Add Observer terminology and pipeline reference
```

---

## Task 1: Create observer _lib.py with shared utilities

**Files:**
- Create: `plugins/dev-team/scripts/observers/_lib.py`
- Test: `tests/observers/test_dispatch.py` (partial — test the utility functions)

- [ ] **Step 1: Create test directory and conftest**

Create `tests/observers/conftest.py`:

```python
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
```

- [ ] **Step 2: Write _lib.py**

Create `plugins/dev-team/scripts/observers/_lib.py`:

```python
"""Shared utilities for observer modules."""

import os
from pathlib import Path


SESSION_BASE = Path(
    os.environ.get(
        "ARBITRATOR_SESSION_BASE",
        os.path.expanduser("~/.agentic-cookbook/dev-team/sessions"),
    )
)


def get_session_log_path(session_id: str) -> Path:
    """Resolve the session.log path for a given session ID.

    Falls back to a default log directory if no session directory exists.
    Creates parent directories as needed.
    """
    session_dir = SESSION_BASE / session_id
    if session_dir.is_dir():
        log_path = session_dir / "session.log"
    else:
        # No active session — write to a general log
        log_dir = SESSION_BASE / "_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "observer.log"
    return log_path
```

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-team/scripts/observers/_lib.py tests/observers/conftest.py
git commit -m "Add observer _lib.py and test fixtures"
```

---

## Task 2: Create dispatch.py — event extraction and auto-discovery

**Files:**
- Create: `plugins/dev-team/scripts/observers/dispatch.py`
- Test: `tests/observers/test_dispatch.py`

- [ ] **Step 1: Write failing tests**

Create `tests/observers/test_dispatch.py`:

```python
"""Tests for observer dispatch — event extraction and auto-discovery."""

import json
import sys
import os
import pytest
from pathlib import Path

# Add the observers directory to sys.path so we can import dispatch
OBSERVERS_DIR = Path(__file__).parent.parent.parent / "plugins" / "dev-team" / "scripts" / "observers"
sys.path.insert(0, str(OBSERVERS_DIR))


def test_extract_event_from_hook_input(sample_transcript_jsonl):
    from dispatch import extract_event

    hook_input = {
        "session_id": "20260406-160200-a1b2",
        "agent_id": "abc123",
        "agent_type": "general-purpose",
        "agent_transcript_path": str(sample_transcript_jsonl),
        "last_assistant_message": "Done. Updated the parser.",
        "hook_event_name": "SubagentStop",
        "cwd": "/Users/test/projects/dev-team",
    }

    event = extract_event(hook_input)

    assert event["session_id"] == "20260406-160200-a1b2"
    assert event["agent_id"] == "abc123"
    assert event["agent_type"] == "general-purpose"
    assert event["status"] == "completed"
    assert event["tool_call_count"] == 2
    assert set(event["tools_used"]) == {"Read", "Write"}
    assert event["transcript_path"] == str(sample_transcript_jsonl)
    assert "timestamp" in event
    assert "summary" in event


def test_extract_event_counts_tools_correctly(tmp_path):
    from dispatch import extract_event

    transcript = tmp_path / "transcript.jsonl"
    lines = [
        {"type": "tool_use", "name": "Read"},
        {"type": "tool_use", "name": "Read"},
        {"type": "tool_use", "name": "Grep"},
        {"type": "tool_use", "name": "Write"},
    ]
    transcript.write_text("\n".join(json.dumps(l) for l in lines) + "\n")

    hook_input = {
        "session_id": "test",
        "agent_id": "test",
        "agent_type": "general-purpose",
        "agent_transcript_path": str(transcript),
        "last_assistant_message": "Done.",
        "hook_event_name": "SubagentStop",
    }

    event = extract_event(hook_input)
    assert event["tool_call_count"] == 4
    assert sorted(event["tools_used"]) == ["Grep", "Read", "Write"]


def test_extract_event_handles_missing_transcript(tmp_path):
    from dispatch import extract_event

    hook_input = {
        "session_id": "test",
        "agent_id": "test",
        "agent_type": "general-purpose",
        "agent_transcript_path": str(tmp_path / "nonexistent.jsonl"),
        "last_assistant_message": "Done.",
        "hook_event_name": "SubagentStop",
    }

    event = extract_event(hook_input)
    assert event["tool_call_count"] == 0
    assert event["tools_used"] == []
    assert event["status"] == "completed"


def test_extract_event_truncates_summary():
    from dispatch import extract_event

    hook_input = {
        "session_id": "test",
        "agent_id": "test",
        "agent_type": "general-purpose",
        "agent_transcript_path": "/nonexistent",
        "last_assistant_message": "x" * 500,
        "hook_event_name": "SubagentStop",
    }

    event = extract_event(hook_input)
    assert len(event["summary"]) <= 200


def test_discover_observers(tmp_path):
    from dispatch import discover_observers

    # Create mock observer modules
    (tmp_path / "stenographer.py").write_text("def observe(event): pass\n")
    (tmp_path / "oslog.py").write_text("def observe(event): pass\n")
    (tmp_path / "_lib.py").write_text("# private\n")
    (tmp_path / "dispatch.py").write_text("# self\n")
    (tmp_path / "not_python.txt").write_text("nope\n")

    observers = discover_observers(tmp_path)
    names = [o.__name__ for o in observers]
    assert "stenographer" in names
    assert "oslog" in names
    assert "_lib" not in names
    assert "dispatch" not in names
    assert len(observers) == 2


def test_discover_observers_skips_modules_without_observe(tmp_path):
    from dispatch import discover_observers

    (tmp_path / "has_observe.py").write_text("def observe(event): pass\n")
    (tmp_path / "no_observe.py").write_text("def something_else(): pass\n")

    observers = discover_observers(tmp_path)
    assert len(observers) == 1


def test_run_observers_isolates_failures(tmp_path, sample_event):
    from dispatch import discover_observers, run_observers

    (tmp_path / "failing.py").write_text("def observe(event): raise ValueError('boom')\n")
    (tmp_path / "passing.py").write_text(
        "results = []\ndef observe(event): results.append(event['agent_id'])\n"
    )

    observers = discover_observers(tmp_path)
    # Should not raise — failures are isolated
    run_observers(observers, sample_event)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_dispatch.py -v`
Expected: FAIL — `dispatch` module doesn't exist yet.

- [ ] **Step 3: Write dispatch.py**

Create `plugins/dev-team/scripts/observers/dispatch.py`:

```python
#!/usr/bin/env python3
"""Observer dispatch — hook entry point.

Called by the SubagentStop hook. Reads hook input from stdin,
extracts a normalized event from the subagent transcript,
and dispatches to all auto-discovered observer modules.
"""

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_event(hook_input: dict) -> dict:
    """Extract a normalized event from SubagentStop hook input."""
    transcript_path = hook_input.get("agent_transcript_path", "")
    tools_used = set()
    tool_call_count = 0

    # Parse transcript JSONL for tool usage stats
    if transcript_path and Path(transcript_path).is_file():
        try:
            with open(transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("type") == "tool_use":
                        tool_call_count += 1
                        name = entry.get("name", "")
                        if name:
                            tools_used.add(name)
        except (OSError, PermissionError):
            pass

    summary = hook_input.get("last_assistant_message", "")
    if len(summary) > 200:
        summary = summary[:197] + "..."

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "session_id": hook_input.get("session_id", ""),
        "agent_id": hook_input.get("agent_id", ""),
        "agent_type": hook_input.get("agent_type", ""),
        "agent_description": hook_input.get("agent_description", ""),
        "status": "completed",
        "duration_ms": 0,
        "tools_used": sorted(tools_used),
        "tool_call_count": tool_call_count,
        "summary": summary,
        "transcript_path": transcript_path,
    }


def discover_observers(observers_dir: Path) -> list:
    """Auto-discover observer modules in the given directory."""
    skip = {"dispatch.py"}
    observers = []

    for py_file in sorted(observers_dir.glob("*.py")):
        if py_file.name in skip or py_file.name.startswith("_"):
            continue

        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Observer {py_file.name} failed to load: {e}", file=sys.stderr)
            continue

        if hasattr(module, "observe"):
            observers.append(module)

    return observers


def run_observers(observers: list, event: dict) -> None:
    """Call observe(event) on each observer. Isolate failures."""
    for module in observers:
        try:
            module.observe(event)
        except Exception as e:
            print(f"Observer {module.__name__} failed: {e}", file=sys.stderr)


def main():
    """Entry point for SubagentStop hook."""
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        print("Failed to read hook input from stdin", file=sys.stderr)
        sys.exit(1)

    event = extract_event(hook_input)
    observers_dir = Path(__file__).parent
    observers = discover_observers(observers_dir)
    run_observers(observers, event)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_dispatch.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-team/scripts/observers/dispatch.py tests/observers/test_dispatch.py
git commit -m "Add observer dispatch with event extraction and auto-discovery"
```

---

## Task 3: Create stenographer observer

**Files:**
- Create: `plugins/dev-team/scripts/observers/stenographer.py`
- Test: `tests/observers/test_stenographer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/observers/test_stenographer.py`:

```python
"""Tests for stenographer observer — session.log JSONL writer."""

import json
import os
import sys
import pytest
from pathlib import Path

OBSERVERS_DIR = Path(__file__).parent.parent.parent / "plugins" / "dev-team" / "scripts" / "observers"
sys.path.insert(0, str(OBSERVERS_DIR))


def test_stenographer_writes_jsonl_line(tmp_session_dir, sample_event):
    os.environ["ARBITRATOR_SESSION_BASE"] = str(tmp_session_dir)

    # Create session directory so stenographer writes there
    session_dir = tmp_session_dir / sample_event["session_id"]
    session_dir.mkdir()

    # Re-import to pick up env var change
    import importlib
    import _lib
    importlib.reload(_lib)
    import stenographer
    importlib.reload(stenographer)

    stenographer.observe(sample_event)

    log_path = session_dir / "session.log"
    assert log_path.exists()

    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["sid"] == sample_event["session_id"]
    assert entry["agent"] == "general-purpose"
    assert entry["desc"] == "Implement Task 4"
    assert entry["status"] == "completed"
    assert entry["calls"] == 16
    assert entry["tools"] == ["Bash", "Read", "Write"]

    os.environ.pop("ARBITRATOR_SESSION_BASE", None)


def test_stenographer_appends_multiple_entries(tmp_session_dir, sample_event):
    os.environ["ARBITRATOR_SESSION_BASE"] = str(tmp_session_dir)

    session_dir = tmp_session_dir / sample_event["session_id"]
    session_dir.mkdir()

    import importlib
    import _lib
    importlib.reload(_lib)
    import stenographer
    importlib.reload(stenographer)

    stenographer.observe(sample_event)
    stenographer.observe(sample_event)

    log_path = session_dir / "session.log"
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 2

    os.environ.pop("ARBITRATOR_SESSION_BASE", None)


def test_stenographer_truncates_summary(tmp_session_dir, sample_event):
    os.environ["ARBITRATOR_SESSION_BASE"] = str(tmp_session_dir)

    session_dir = tmp_session_dir / sample_event["session_id"]
    session_dir.mkdir()

    import importlib
    import _lib
    importlib.reload(_lib)
    import stenographer
    importlib.reload(stenographer)

    sample_event["summary"] = "x" * 500
    stenographer.observe(sample_event)

    log_path = session_dir / "session.log"
    entry = json.loads(log_path.read_text().strip())
    assert len(entry["summary"]) <= 200

    os.environ.pop("ARBITRATOR_SESSION_BASE", None)


def test_stenographer_falls_back_to_general_log(tmp_session_dir, sample_event):
    os.environ["ARBITRATOR_SESSION_BASE"] = str(tmp_session_dir)

    # Don't create the session directory — should fall back
    import importlib
    import _lib
    importlib.reload(_lib)
    import stenographer
    importlib.reload(stenographer)

    stenographer.observe(sample_event)

    fallback_log = tmp_session_dir / "_logs" / "observer.log"
    assert fallback_log.exists()

    os.environ.pop("ARBITRATOR_SESSION_BASE", None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_stenographer.py -v`
Expected: FAIL — `stenographer` module doesn't exist.

- [ ] **Step 3: Write stenographer.py**

Create `plugins/dev-team/scripts/observers/stenographer.py`:

```python
"""Stenographer observer — writes structured JSONL to session.log."""

import json
from _lib import get_session_log_path


def observe(event: dict) -> None:
    """Append a log entry to the session log."""
    summary = event.get("summary", "")
    if len(summary) > 200:
        summary = summary[:197] + "..."

    log_entry = {
        "ts": event["timestamp"],
        "sid": event["session_id"],
        "agent": event["agent_type"],
        "desc": event.get("agent_description", ""),
        "status": event["status"],
        "duration_ms": event.get("duration_ms", 0),
        "tools": event.get("tools_used", []),
        "calls": event.get("tool_call_count", 0),
        "summary": summary,
    }

    log_path = get_session_log_path(event["session_id"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_stenographer.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-team/scripts/observers/stenographer.py tests/observers/test_stenographer.py
git commit -m "Add stenographer observer — session.log JSONL writer"
```

---

## Task 4: Create oslog observer

**Files:**
- Create: `plugins/dev-team/scripts/observers/oslog.py`
- Test: `tests/observers/test_oslog.py`

- [ ] **Step 1: Write failing tests**

Create `tests/observers/test_oslog.py`:

```python
"""Tests for oslog observer — system log writer."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

OBSERVERS_DIR = Path(__file__).parent.parent.parent / "plugins" / "dev-team" / "scripts" / "observers"
sys.path.insert(0, str(OBSERVERS_DIR))


def test_oslog_formats_message_correctly(sample_event):
    import oslog

    msg = oslog.format_message(sample_event)
    assert "[dev-team]" in msg
    assert "general-purpose" in msg
    assert "Implement Task 4" in msg
    assert "completed" in msg
    assert "45s" in msg
    assert "16 calls" in msg


def test_oslog_formats_short_description(sample_event):
    import oslog

    sample_event["agent_description"] = ""
    msg = oslog.format_message(sample_event)
    # Falls back to agent_type when no description
    assert "general-purpose" in msg


def test_oslog_calls_logger(sample_event):
    import oslog

    with patch("oslog.subprocess.run") as mock_run:
        oslog.observe(sample_event)
        mock_run.assert_called_once()
        args = mock_run.call_args
        cmd = args[0][0]
        assert cmd[0] == "logger"
        assert "-t" in cmd
        assert "dev-team" in cmd


def test_oslog_silently_handles_missing_logger(sample_event):
    import oslog

    with patch("oslog.subprocess.run", side_effect=FileNotFoundError):
        # Should not raise
        oslog.observe(sample_event)


def test_oslog_silently_handles_timeout(sample_event):
    import oslog
    import subprocess

    with patch("oslog.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="logger", timeout=5)):
        # Should not raise
        oslog.observe(sample_event)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_oslog.py -v`
Expected: FAIL — `oslog` module doesn't exist.

- [ ] **Step 3: Write oslog.py**

Create `plugins/dev-team/scripts/observers/oslog.py`:

```python
"""System log observer — writes one-liners via POSIX logger CLI."""

import subprocess


def format_message(event: dict) -> str:
    """Format a human-readable one-liner for the system log."""
    desc = event.get("agent_description", "") or event["agent_type"]
    status = event["status"]
    duration = event.get("duration_ms", 0) // 1000
    calls = event.get("tool_call_count", 0)
    return f'[dev-team] {event["agent_type"]} "{desc}" {status} ({duration}s, {calls} calls)'


def observe(event: dict) -> None:
    """Write event to system log via logger CLI."""
    msg = format_message(event)
    try:
        subprocess.run(
            ["logger", "-t", "dev-team", "-p", "user.info", msg],
            timeout=5,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/test_oslog.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-team/scripts/observers/oslog.py tests/observers/test_oslog.py
git commit -m "Add oslog observer — system log via logger CLI"
```

---

## Task 5: Create settings.json with SubagentStop hook

**Files:**
- Create: `.claude/settings.json`

- [ ] **Step 1: Create settings.json**

Create `.claude/settings.json`:

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/observers/dispatch.py"
          }
        ]
      }
    ]
  }
}
```

Note: If `${CLAUDE_PLUGIN_ROOT}` is not available in the hook context, use the absolute path pattern. Check how other hooks in the project reference plugin paths. If no other hooks exist, use a relative path from the project root:

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 plugins/dev-team/scripts/observers/dispatch.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add .claude/settings.json
git commit -m "Add SubagentStop hook for observer dispatch"
```

---

## Task 6: Update architecture.md

**Files:**
- Modify: `docs/architecture.md`

- [ ] **Step 1: Add observer terminology**

In the Terminology table in `docs/architecture.md`, add after the Consulting-Verifier row:

```markdown
| **Observer** | Shell hook + Python script that captures subagent activity via `SubagentStop`. Auto-discovers observer modules in `scripts/observers/`. |
| **Stenographer** | Built-in observer. Writes structured JSONL session log to the session directory. |
```

- [ ] **Step 2: Add to pipeline description**

In the pipeline diagram, add a note that observers run at the system level:

```
          → Specialty-teams run (worker-verifier loop, max 3 retries)
          → Consulting-teams review (if any — worker-verifier loop per consultant)
          → Specialist-persona writes interpretations
          [Observer hook fires on each subagent completion — writes session.log + system log]
```

- [ ] **Step 3: Update file map**

Add to the file map under scripts/:

```
      observers/                # Observer modules (auto-discovered by SubagentStop hook)
        dispatch.py             # Hook entry point — event extraction + observer dispatch
        stenographer.py         # Session.log JSONL writer
        oslog.py                # System log writer (macOS/Linux)
```

- [ ] **Step 4: Commit**

```bash
git add docs/architecture.md
git commit -m "Add observer system to architecture docs"
```

---

## Task 7: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run observer tests**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/observers/ -v`
Expected: All tests PASS (dispatch: 7, stenographer: 4, oslog: 5 = 16 total).

- [ ] **Step 2: Run existing arbitrator tests (no regressions)**

Run: `cd /Users/mfullerton/projects/active/dev-team && python3 -m pytest tests/arbitrator/ -v`
Expected: All 72 tests PASS.

- [ ] **Step 3: Manual test — dispatch.py with mock stdin**

Run:

```bash
cd /Users/mfullerton/projects/active/dev-team

# Create a mock transcript
echo '{"type":"tool_use","name":"Read"}' > /tmp/test-transcript.jsonl
echo '{"type":"assistant","content":"Done."}' >> /tmp/test-transcript.jsonl

# Create a session directory for the log
mkdir -p ~/.agentic-cookbook/dev-team/sessions/test-observer

# Feed mock hook input to dispatch
echo '{"session_id":"test-observer","agent_id":"test","agent_type":"general-purpose","agent_transcript_path":"/tmp/test-transcript.jsonl","last_assistant_message":"Done.","hook_event_name":"SubagentStop"}' | python3 plugins/dev-team/scripts/observers/dispatch.py

# Check session.log was written
cat ~/.agentic-cookbook/dev-team/sessions/test-observer/session.log

# Check system log
log show --predicate 'eventMessage CONTAINS "dev-team"' --last 1m 2>/dev/null || echo "log show not available or no entries"

# Cleanup
rm -rf ~/.agentic-cookbook/dev-team/sessions/test-observer
rm /tmp/test-transcript.jsonl
```

Expected: session.log contains one JSONL line. System log shows a `[dev-team]` entry.

- [ ] **Step 4: Verify auto-discovery by adding a dummy observer**

```bash
# Create a temporary observer
echo 'def observe(event): print(f"TEST: {event[\"agent_type\"]}")' > plugins/dev-team/scripts/observers/_test_dummy.py

echo '{"session_id":"test","agent_id":"test","agent_type":"dummy-test","agent_transcript_path":"/nonexistent","last_assistant_message":"test","hook_event_name":"SubagentStop"}' | python3 plugins/dev-team/scripts/observers/dispatch.py

# Should NOT print "TEST: dummy-test" because it starts with _
# Remove it
rm plugins/dev-team/scripts/observers/_test_dummy.py

# Now without underscore
echo 'def observe(event): print(f"TEST: {event[\"agent_type\"]}")' > plugins/dev-team/scripts/observers/test_dummy.py

echo '{"session_id":"test","agent_id":"test","agent_type":"dummy-test","agent_transcript_path":"/nonexistent","last_assistant_message":"test","hook_event_name":"SubagentStop"}' | python3 plugins/dev-team/scripts/observers/dispatch.py

# Should print "TEST: dummy-test"
rm plugins/dev-team/scripts/observers/test_dummy.py
```
