import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_session_dir(tmp_path):
    """Each test gets its own session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    os.environ["TEAM_PIPELINE_SESSION_BASE"] = str(session_dir)
    yield session_dir
    os.environ.pop("TEAM_PIPELINE_SESSION_BASE", None)
