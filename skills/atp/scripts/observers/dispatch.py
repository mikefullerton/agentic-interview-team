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
