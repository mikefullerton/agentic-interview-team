"""Shared test fixtures for rollcall unit tests.

Mirrors the integration_surface conftest's sys.path insertion so
`from services.integration_surface import ...` and
`from services.rollcall import ...` both resolve.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

FIXTURE_TEAM = REPO_ROOT / "testing" / "fixtures" / "teams" / "rollcall_team"


@pytest.fixture
def fixture_team_root() -> Path:
    return FIXTURE_TEAM


@pytest.fixture
def run_async():
    def runner(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
    return runner
