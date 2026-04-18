"""Shared fixtures for the rollcall real-LLM smoke.

Extends sys.path so the rollcall orchestrator + integration surface are
importable when pytest is invoked from the repo root. The test is
gated by `AGENTIC_REAL_LLM_SMOKE=1`; without it, every test under this
directory is skipped at collection time.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


_THIS_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(config, items):
    gate_on = os.environ.get("AGENTIC_REAL_LLM_SMOKE") == "1"
    if gate_on:
        return
    skip = pytest.mark.skip(
        reason="rollcall real-LLM smoke gated by AGENTIC_REAL_LLM_SMOKE=1"
    )
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        if _THIS_DIR in item_path.parents:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def claude_bin() -> str:
    path = shutil.which("claude")
    if path is None:
        pytest.skip("claude CLI not found on PATH")
    return path


@pytest.fixture(scope="session")
def puppy_team_root() -> Path:
    root = REPO_ROOT / "teams" / "puppynamingteam"
    if not root.is_dir():
        pytest.skip(f"teams/puppynamingteam not found at {root}")
    return root
