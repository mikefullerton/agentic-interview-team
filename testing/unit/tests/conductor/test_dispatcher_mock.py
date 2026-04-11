"""MockDispatcher smoke tests."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from services.conductor.dispatcher import (
    AgentDefinition,
    DispatchCorrelation,
    DispatchError,
    MockDispatcher,
)


def _corr(agent: str = "a") -> DispatchCorrelation:
    return DispatchCorrelation(
        session_id=uuid4(),
        team_id="t",
        agent_id=agent,
        dispatch_id=f"d_{agent}",
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
            correlation=_corr("echo"),
            event_sink=sink,
        )
        assert result.response == {"echoed": "hello"}

    asyncio.run(_t())


def test_mock_dispatcher_missing_preset_raises_typed_error():
    """Missing agent in preset → DispatchError, not AttributeError/KeyError."""

    async def _t():
        d = MockDispatcher()

        async def sink(_):
            return None

        with pytest.raises(DispatchError) as exc_info:
            await d.dispatch(
                agent=AgentDefinition(name="missing", prompt="x"),
                prompt="hi",
                logical_model="balanced",
                response_schema=None,
                correlation=_corr("missing"),
                event_sink=sink,
            )
        assert "missing" in str(exc_info.value)

    asyncio.run(_t())


def test_mock_dispatcher_events_arrive_in_order():
    """Event sink receives start and complete events in that order."""

    async def _t():
        d = MockDispatcher({"a": {"x": 1}})
        seen: list[str] = []

        async def sink(evt):
            seen.append(evt["kind"])

        await d.dispatch(
            agent=AgentDefinition(name="a", prompt="p"),
            prompt="p",
            logical_model="balanced",
            response_schema=None,
            correlation=_corr("a"),
            event_sink=sink,
        )
        assert seen == ["dispatch_start", "dispatch_complete"]

    asyncio.run(_t())


def test_mock_dispatcher_is_reentrant_under_gather():
    """Two concurrent dispatches on the same MockDispatcher must not cross contaminate."""

    async def _t():
        d = MockDispatcher(
            {
                "a": lambda p: {"who": "a", "prompt": p},
                "b": lambda p: {"who": "b", "prompt": p},
            }
        )

        async def noop(_):
            return None

        async def call(name: str, prompt: str):
            return await d.dispatch(
                agent=AgentDefinition(name=name, prompt="x"),
                prompt=prompt,
                logical_model="balanced",
                response_schema=None,
                correlation=_corr(name),
                event_sink=noop,
            )

        ra, rb = await asyncio.gather(call("a", "p-a"), call("b", "p-b"))
        assert ra.response == {"who": "a", "prompt": "p-a"}
        assert rb.response == {"who": "b", "prompt": "p-b"}

    asyncio.run(_t())
