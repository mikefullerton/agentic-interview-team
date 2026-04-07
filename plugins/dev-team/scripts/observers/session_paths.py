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
