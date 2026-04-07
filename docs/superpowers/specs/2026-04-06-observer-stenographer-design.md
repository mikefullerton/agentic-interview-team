# Observer System + Stenographer Design

## Summary

Add an observer system to the dev-team pipeline that captures raw subagent activity via a Claude Code `SubagentStop` hook. Observers are auto-discovered Python modules that each receive a normalized event and do one thing with it. The first two built-in observers are the **stenographer** (writes structured session log via storage-provider) and **oslog** (writes one-liners to macOS/Linux system log).

## Motivation

The current pipeline discards the process narrative. Each participant produces structured output (findings, verdicts), but how they got there — what they read, what they noticed, what they tried — evaporates after the session. The observer system captures this at the system level via hooks, with zero changes to existing agents or orchestration.

## Architecture

```
SubagentStop hook fires (system-level, settings.json)
  → dispatch.py reads hook input from stdin
  → Reads agent transcript JSONL (full raw output)
  → Extracts normalized event
  → Auto-discovers observer modules in scripts/observers/
  → Calls each observer's observe(event) function
```

### Key Properties

- **Zero agent changes** — observers are invisible to participants
- **Deterministic** — no LLM involved, pure data extraction
- **Extensible** — drop a .py file in the observers directory, it runs
- **Dual-write** — session log (structured, queryable) + system log (real-time monitoring)
- **Crash-safe** — each observer writes independently; one failure doesn't block others

## Hook Configuration

In the project's `.claude/settings.json`:

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

The hook fires on every subagent completion. The matcher is empty (match all subagents). `dispatch.py` is the sole entry point.

## Event Extraction (`dispatch.py`)

### Input

`SubagentStop` provides via stdin:

```json
{
  "session_id": "abc123",
  "agent_id": "a1b2c3d4",
  "agent_type": "general-purpose",
  "agent_transcript_path": "/path/to/transcript.jsonl",
  "last_assistant_message": "...",
  "cwd": "/Users/.../dev-team",
  "hook_event_name": "SubagentStop"
}
```

### Transcript JSONL

The `agent_transcript_path` points to a JSONL file with the full subagent conversation. Each line is a turn — tool calls, tool results, assistant messages. `dispatch.py` reads this to extract:

- Which tools were called and how many times
- Key outputs (findings, verdicts, file paths)
- Duration (first timestamp to last)
- Whether the agent completed successfully or errored

### Normalized Event Output

```python
{
    "timestamp": "2026-04-06T16:02:03.000Z",
    "session_id": "abc123",
    "agent_id": "a1b2c3d4",
    "agent_type": "general-purpose",
    "agent_description": "Implement Task 4: parse consulting teams",
    "status": "completed",
    "duration_ms": 45000,
    "tools_used": ["Read", "Write", "Bash"],
    "tool_call_count": 16,
    "summary": "...",
    "transcript_path": "/path/to/transcript.jsonl"
}
```

The `agent_description` is extracted from the Agent tool's `description` parameter (the 3-5 word task summary). The `summary` is `last_assistant_message` truncated to a reasonable length. The `transcript_path` is included so observers that need raw data can read the full transcript.

## Observer Interface

Each observer is a Python file in `scripts/observers/` that implements:

```python
def observe(event: dict) -> None:
    """Receive a normalized event. Do one thing with it."""
```

### Auto-Discovery

`dispatch.py` scans `scripts/observers/` for `.py` files (excluding `dispatch.py` and files starting with `_`). For each, it imports the module and calls `observe(event)`. Observers run sequentially. If one raises an exception, it's logged to stderr and the next observer runs.

```python
# dispatch.py auto-discovery logic
observer_dir = Path(__file__).parent
for py_file in sorted(observer_dir.glob("*.py")):
    if py_file.name in ("dispatch.py",) or py_file.name.startswith("_"):
        continue
    module = import_module_from_path(py_file)
    if hasattr(module, "observe"):
        try:
            module.observe(event)
        except Exception as e:
            print(f"Observer {py_file.name} failed: {e}", file=sys.stderr)
```

### Adding a New Observer

1. Create `scripts/observers/my_observer.py`
2. Implement `def observe(event: dict) -> None:`
3. Done — auto-discovered on next subagent completion

No registration, no config, no manifest.

## Built-in Observers

### 1. Stenographer (`stenographer.py`)

Appends structured JSONL to the session log. Uses the storage-provider abstraction so the backend is swappable.

**Output path:** Determined by the storage-provider. For the markdown backend: `~/.agentic-cookbook/dev-team/sessions/<session-id>/session.log`

**Log entry format (one JSONL line per event):**

```json
{"ts":"2026-04-06T16:02:03Z","sid":"abc123","agent":"general-purpose","desc":"Implement Task 4","status":"completed","duration_ms":45000,"tools":["Read","Write","Bash"],"calls":16,"summary":"Updated run_specialty_teams.py..."}
```

**Implementation:**

```python
def observe(event: dict) -> None:
    log_entry = {
        "ts": event["timestamp"],
        "sid": event["session_id"],
        "agent": event["agent_type"],
        "desc": event.get("agent_description", ""),
        "status": event["status"],
        "duration_ms": event.get("duration_ms", 0),
        "tools": event.get("tools_used", []),
        "calls": event.get("tool_call_count", 0),
        "summary": event.get("summary", "")[:200],
    }
    log_path = get_session_log_path(event["session_id"])
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
```

The `get_session_log_path` function resolves the path through the storage-provider (or falls back to a default location if no active session).

### 2. System Log (`oslog.py`)

Writes one-liner to the platform system log.

**macOS/Linux:** Uses `logger` CLI (POSIX, routes to unified log on macOS, syslog/journald on Linux).

**Format:**

```
[dev-team] general-purpose "Implement Task 4" completed (45s, 16 calls)
[dev-team] specialty-team-worker "security/authentication" completed (12s, 8 calls)
[dev-team] consulting-team-worker "cross-db-compat reviewing primary-keys" completed (8s, 4 calls)
```

**Implementation:**

```python
import subprocess

def observe(event: dict) -> None:
    desc = event.get("agent_description", event["agent_type"])
    status = event["status"]
    duration = event.get("duration_ms", 0) // 1000
    calls = event.get("tool_call_count", 0)
    msg = f'[dev-team] {event["agent_type"]} "{desc}" {status} ({duration}s, {calls} calls)'

    try:
        subprocess.run(
            ["logger", "-t", "dev-team", "-p", "user.info", msg],
            timeout=5, capture_output=True
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # logger not available or hung — silent fail
```

Silent fail on missing `logger` — Windows doesn't have it, and this observer is non-critical.

## File Structure

### New files

```
plugins/dev-team/
  scripts/
    observers/
      _lib.py              # Shared utilities (path resolution, etc.)
      dispatch.py           # Hook entry point — reads stdin, extracts event, calls observers
      stenographer.py       # Writes session.log via storage-provider
      oslog.py              # Writes to system log via logger CLI

.claude/
  settings.json             # SubagentStop hook configuration (may need to modify existing)

tests/
  observers/
    test_dispatch.py        # Tests event extraction from mock transcript
    test_stenographer.py    # Tests log entry format and append behavior
    test_oslog.py           # Tests message formatting (not actual logger call)
```

### Modified files

```
docs/
  architecture.md           # Add Observer section to terminology and pipeline
```

## Scope

### In scope
- Hook configuration in settings.json
- `dispatch.py` entry point with auto-discovery
- Event extraction from transcript JSONL
- Stenographer observer (session.log JSONL)
- System log observer (logger CLI)
- Tests for event extraction and observer output format
- Architecture docs update

### Out of scope
- Dashboard WebSocket observer (future)
- Modifying any existing agents or orchestration
- Storage-provider changes (stenographer writes directly to the session directory for now; full storage-provider integration is a follow-up if needed)
- Windows Event Log support (logger CLI handles macOS/Linux; Windows silently skips)

## Testing

- **Event extraction:** Mock transcript JSONL → verify normalized event has correct fields
- **Stenographer:** Mock event → verify JSONL line format and append behavior
- **Oslog:** Mock event → verify formatted message string (don't call actual logger in tests)
- **Auto-discovery:** Verify dispatch.py finds observer modules, skips `_` prefixed and dispatch.py itself
- **Error isolation:** Verify one observer throwing doesn't prevent others from running
