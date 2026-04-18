"""Real-LLM smoke of the puppy roadmap via ClaudeCodeDispatcher.

Skipped by default because it shells out to `claude -p` and incurs
real token cost. Enable by setting AGENTIC_REAL_LLM_SMOKE=1 in the
environment before running pytest.

What it proves:
- The ClaudeCodeDispatcher correctly invokes the real Claude CLI
- Structured JSON responses round-trip through the dispatcher
- WhatsNextSpecialty + the puppy realizer produce a ranked name list
  against real model outputs

Not asserting specific names — just that the flow completes, every
primitive reaches `done`, and the final presented message contains
a non-empty ranked list.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import Arbitrator, SessionStatus  # noqa: E402
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import ClaudeCodeDispatcher  # noqa: E402
from services.conductor.playbooks.name_a_puppy_roadmap import (  # noqa: E402
    TEAM_ID,
    build_roadmap,
    realize,
)
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402


pytestmark = pytest.mark.skipif(
    os.environ.get("AGENTIC_REAL_LLM_SMOKE") != "1",
    reason="Set AGENTIC_REAL_LLM_SMOKE=1 to run real-LLM smoke (cost).",
)


def test_puppy_roadmap_with_real_llm(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap_id = await build_roadmap(arb)
        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id=TEAM_ID,
            roadmap_id=roadmap_id,
        )

        dispatcher = ClaudeCodeDispatcher()
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
            max_steps=50,
        )
        await conductor.run_roadmap(
            [WhatsNextSpecialty()],
            realize_primitive=realize,
        )

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        for node_id in (
            "gather-traits",
            "breed-names",
            "lifestyle-names",
            "temperament-names",
            "aggregate",
            "present",
        ):
            latest = await arb.latest_node_state(node_id)
            assert latest is not None
            assert latest.event_type.value == "done", (
                f"{node_id} ended in {latest.event_type.value}"
            )

        messages = await arb.list_messages(session_id)
        present_body = messages[-1].body
        assert "Top candidate names:" in present_body
        # At least one ranked entry rendered.
        assert "1." in present_body
        await arb.close()

    asyncio.run(_t())
