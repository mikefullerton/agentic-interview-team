import os
import sys
from pathlib import Path
import pytest

# Ensure this directory is first on sys.path so 'helpers' resolves to our helpers.py
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def isolated_session_dir(tmp_path):
    """Each test gets its own session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    os.environ["ARBITRATOR_SESSION_BASE"] = str(session_dir)
    yield session_dir
    os.environ.pop("ARBITRATOR_SESSION_BASE", None)
