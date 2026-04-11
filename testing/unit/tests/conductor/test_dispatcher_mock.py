"""MockDispatcher smoke tests."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.dispatcher import (  # noqa: E402
    AgentDefinition,
    DispatchCorrelation,
    MockDispatcher,
)


def test_mock_dispatcher_returns_preset_response():
    async def _t():
        d = MockDispatcher({"picker": {"name": "Luna"}})
        events: list[dict] = []

        async def sink(e):
            events.append(e)

        result = await d.dispatch(
            agent=AgentDefinition(name="picker", prompt="pick a name"),
            prompt="hi",
            logical_model="balanced",
            response_schema=None,
            correlation=DispatchCorrelation(
                session_id=uuid4(),
                team_id="name-a-puppy",
                agent_id="picker",
                dispatch_id="disp_1",
            ),
            event_sink=sink,
        )
        assert result.terminated_normally is True
        assert result.response == {"name": "Luna"}
        assert len(events) == 2  # start + complete

    asyncio.run(_t())


def test_mock_dispatcher_callable_response():
    async def _t():
        d = MockDispatcher()
        d.set_response("echo", lambda p: {"echoed": p})

        async def sink(_):
            return None

        result = await d.dispatch(
            agent=AgentDefinition(name="echo", prompt="echo"),
            prompt="hello",
            logical_model="fast-cheap",
            response_schema=None,
            correlation=DispatchCorrelation(
                session_id=uuid4(),
                team_id="t",
                agent_id="echo",
                dispatch_id="d",
            ),
            event_sink=sink,
        )
        assert result.response == {"echoed": "hello"}

    asyncio.run(_t())
