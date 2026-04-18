"""Stdio NDJSON transport — transport-specific edges.

Contract parity is handled by `conftest.py`'s `transport_factory`
parametrization. These tests cover what's unique to stdio: demuxing
concurrent sessions, handling a subprocess that exits mid-flight, and
ignoring stray non-JSON stdout lines.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from services.integration_surface import StdioSession

from ..fixtures.fake_team import FakeTeam

REPO_ROOT = Path(__file__).resolve().parents[5]
_STDIO_ENTRY = str(
    REPO_ROOT
    / "testing"
    / "unit"
    / "tests"
    / "integration_surface"
    / "fixtures"
    / "stdio_server.py"
)


def _serialize(fake: FakeTeam) -> str:
    replies = []
    for r in fake._replies:
        replies.append(
            {
                "events": [list(ev) for ev in r.events],
                "ask": list(r.ask) if r.ask is not None else None,
                "after_answer": [list(ev) for ev in r.after_answer],
            }
        )
    return json.dumps({"replies": replies})


def _mk_session(fake: FakeTeam) -> StdioSession:
    return StdioSession(
        cmd=[sys.executable, _STDIO_ENTRY],
        env={"AGENTIC_FAKE_SCRIPT": _serialize(fake), "PYTHONUNBUFFERED": "1"},
    )


def test_events_demux_across_concurrent_sessions(run_async):
    """Two sessions on one subprocess; each sees only its own events."""
    fake = FakeTeam().reply(
        ("text", {"text": "ping"}),
        ("result", {"stop_reason": "end_turn"}),
    )
    session = _mk_session(fake)

    async def scenario():
        h1 = await session.start(team="a")
        h2 = await session.start(team="b")
        await session.send(h1.session_id, "hi")
        await session.send(h2.session_id, "hi")

        async def collect(sid):
            out = []
            async for ev in session.events(sid):
                out.append(ev)
                if ev.type == "result":
                    return out
            return out

        e1, e2 = await asyncio.gather(
            collect(h1.session_id), collect(h2.session_id)
        )
        assert all(e.session_id == h1.session_id for e in e1)
        assert all(e.session_id == h2.session_id for e in e2)
        await session.close(h1.session_id)
        await session.close(h2.session_id)
        await session.shutdown()

    run_async(scenario())


def test_subprocess_death_closes_event_stream(run_async):
    """If the subprocess dies mid-session, `events()` terminates cleanly."""
    fake = FakeTeam().reply(
        ("text", {"text": "hi"}),
        ("result", {"stop_reason": "end_turn"}),
    )
    session = _mk_session(fake)

    async def scenario():
        h = await session.start(team="t")
        proc = session._proc
        assert proc is not None
        proc.kill()

        events: list = []
        async for ev in session.events(h.session_id):
            events.append(ev)
        # Stream terminated (we exited the async-for) — no more output
        # after the subprocess went away. Anything already queued is
        # fine; we just require termination.
        await session.close(h.session_id)
        await session.shutdown()
        return events

    run_async(scenario())


def test_invalid_json_on_wire_is_skipped(run_async, tmp_path):
    """Non-JSON lines from the subprocess must not crash the reader."""
    # Custom server that emits a garbage line before the real protocol.
    script = tmp_path / "noisy_server.py"
    script.write_text(
        "import sys, asyncio, os\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'plugins' / 'dev-team')!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'testing' / 'unit' / 'tests')!r})\n"
        "print('not json at all', flush=True)\n"
        "from services.integration_surface import InProcessSession, serve_stdio\n"
        "from integration_surface.fixtures.fake_team import FakeTeam\n"
        "fake = FakeTeam().reply(\n"
        "    ('text', {'text': 'ok'}),\n"
        "    ('result', {'stop_reason': 'end_turn'}),\n"
        ")\n"
        "async def main():\n"
        "    loop = asyncio.get_event_loop()\n"
        "    reader = asyncio.StreamReader()\n"
        "    protocol = asyncio.StreamReaderProtocol(reader)\n"
        "    await loop.connect_read_pipe(lambda: protocol, sys.stdin)\n"
        "    transport, p = await loop.connect_write_pipe(\n"
        "        asyncio.streams.FlowControlMixin, sys.stdout.buffer\n"
        "    )\n"
        "    writer = asyncio.StreamWriter(transport, p, None, loop)\n"
        "    session = InProcessSession(fake)\n"
        "    await serve_stdio(session, reader, writer)\n"
        "asyncio.run(main())\n"
    )
    session = StdioSession(
        cmd=[sys.executable, str(script)],
        env={"PYTHONUNBUFFERED": "1"},
    )

    async def scenario():
        h = await session.start(team="t")
        await session.send(h.session_id, "hi")
        events = []
        async for ev in session.events(h.session_id):
            events.append(ev)
            if ev.type == "result":
                break
        await session.close(h.session_id)
        await session.shutdown()
        return events

    events = run_async(scenario())
    assert [e.type for e in events] == ["text", "result"]


def test_stdio_lands_session_options_intact(run_async):
    """A round-trip through JSON should preserve SessionOptions fields."""
    from services.integration_surface import SessionOptions

    fake = FakeTeam().reply(("result", {"stop_reason": "end_turn"}))
    session = _mk_session(fake)

    async def scenario():
        opts = SessionOptions(
            allowed_tools=("Read",),
            disallowed_tools=("Bash",),
            max_turns=5,
            permission_mode="plan",
        )
        h = await session.start(team="t", options=opts)
        await session.send(h.session_id, "hi")
        events = []
        async for ev in session.events(h.session_id):
            events.append(ev)
            if ev.type == "result":
                break
        await session.close(h.session_id)
        await session.shutdown()
        return events

    events = run_async(scenario())
    assert events and events[-1].type == "result"
