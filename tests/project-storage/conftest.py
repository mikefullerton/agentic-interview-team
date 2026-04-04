import os
import sys
from pathlib import Path
import pytest

# Ensure this directory is first on sys.path so 'helpers' resolves to our helpers.py
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def isolated_project_dir(tmp_path):
    """Each test gets its own working directory."""
    os.chdir(str(tmp_path))
    yield tmp_path
