"""Stenographer observer — writes structured JSONL to session.log."""

import json
from session_paths import get_session_log_path


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
        "tools": sorted(event.get("tools_used", [])),
        "calls": event.get("tool_call_count", 0),
        "summary": summary,
    }

    log_path = get_session_log_path(event["session_id"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
