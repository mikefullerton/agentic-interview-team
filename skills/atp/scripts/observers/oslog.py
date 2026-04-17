"""System log observer — writes one-liners via POSIX logger CLI."""

import subprocess


def format_message(event: dict) -> str:
    """Format a human-readable one-liner for the system log."""
    desc = event.get("agent_description", "") or event["agent_type"]
    status = event["status"]
    duration = event.get("duration_ms", 0) // 1000
    calls = event.get("tool_call_count", 0)
    return f'[team-pipeline] {event["agent_type"]} "{desc}" {status} ({duration}s, {calls} calls)'


def observe(event: dict) -> None:
    """Write event to system log via logger CLI."""
    msg = format_message(event)
    try:
        subprocess.run(
            ["logger", "-t", "team-pipeline", "-p", "user.info", msg],
            timeout=5,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
