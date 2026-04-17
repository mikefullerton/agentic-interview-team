"""Shared utilities for observer modules."""

import os
from pathlib import Path


SESSION_BASE = Path(
    os.environ.get(
        "TEAM_PIPELINE_SESSION_BASE",
        os.path.expanduser("~/.team-pipeline/sessions"),
    )
)


def get_session_log_path(session_id: str) -> Path:
    """Resolve the session.log path for a given session ID."""
    session_dir = SESSION_BASE / session_id
    if session_dir.is_dir():
        log_path = session_dir / "session.log"
    else:
        log_dir = SESSION_BASE / "_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "observer.log"
    return log_path
