"""WebSocket transport — transport-specific edges.

Contract parity is handled by `conftest.py`'s `transport_factory`
parametrization. These tests cover what's unique to websockets:
connection loss, invalid frames, and concurrent-session demux across
one socket.
"""
from __future__ import annotations

import asyncio
import json

import pytest

websockets = pytest.importorskip("websockets")
from websockets.asyncio.server import serve  # noqa: E402

from services.integration_surface import (  # noqa: E402
    InProcessSession,
    SessionOptions,
    WebSocketSession,
    serve_websocket,
)

from ..fixtures.fake_team import FakeTeam  # noqa: E402


async def _start_server(runner):
    server_session = InProcessSession(runner)

    async def handler(ws):
        await serve_websocket(server_session, ws)

    cm = serve(handler, "localhost", 0)
    server = await cm.__aenter__()
    port = server.sockets[0].getsockname()[1]
    return cm, server, port


def test_events_demux_across_concurrent_sessions(run_async):
    """Two sessions on one socket; each sees only its own events."""
    fake = FakeTeam().reply(
        ("text", {"text": "ping"}),
        ("result", {"stop_reason": "end_turn"}),
    )

    async def scenario():
        cm, _server, port = await _start_server(fake)
        client = WebSocketSession(f"ws://localhost:{port}")
        try:
            h1 = await client.start(team="a")
            h2 = await client.start(team="b")
            await client.send(h1.session_id, "hi")
            await client.send(h2.session_id, "hi")

            async def collect(sid):
                out = []
                async for ev in client.events(sid):
                    out.append(ev)
                    if ev.type == "result":
                        return out
                return out

            e1, e2 = await asyncio.gather(
                collect(h1.session_id), collect(h2.session_id)
            )
            assert all(e.session_id == h1.session_id for e in e1)
            assert all(e.session_id == h2.session_id for e in e2)
            await client.close(h1.session_id)
            await client.close(h2.session_id)
        finally:
            await client.shutdown()
            await cm.__aexit__(None, None, None)

    run_async(scenario())


def test_connection_loss_terminates_event_stream(run_async):
    """If the server closes the socket, `events()` ends cleanly."""
    fake = FakeTeam().reply(
        ("text", {"text": "hi"}),
        ("result", {"stop_reason": "end_turn"}),
    )

    async def scenario():
        cm, server, port = await _start_server(fake)
        client = WebSocketSession(f"ws://localhost:{port}")
        try:
            h = await client.start(team="t")
            # Forcibly close the server side.
            server.close()
            await server.wait_closed()

            events = []
            async for ev in client.events(h.session_id):
                events.append(ev)
            await client.close(h.session_id)
        finally:
            await client.shutdown()
            try:
                await cm.__aexit__(None, None, None)
            except Exception:
                pass

    run_async(scenario())


def test_invalid_json_frame_is_skipped(run_async):
    """Non-JSON text frames from the server must not crash the reader."""
    fake = FakeTeam().reply(
        ("text", {"text": "ok"}),
        ("result", {"stop_reason": "end_turn"}),
    )

    async def scenario():
        server_session = InProcessSession(fake)

        async def handler(ws):
            # Slip a garbage frame through before the real protocol.
            await ws.send("not json at all")
            await serve_websocket(server_session, ws)

        cm = serve(handler, "localhost", 0)
        server = await cm.__aenter__()
        port = server.sockets[0].getsockname()[1]
        client = WebSocketSession(f"ws://localhost:{port}")
        try:
            h = await client.start(team="t")
            await client.send(h.session_id, "hi")
            events = []
            async for ev in client.events(h.session_id):
                events.append(ev)
                if ev.type == "result":
                    break
            await client.close(h.session_id)
            return events
        finally:
            await client.shutdown()
            await cm.__aexit__(None, None, None)

    events = run_async(scenario())
    assert [e.type for e in events] == ["text", "result"]


def test_session_options_round_trip_through_wire(run_async):
    """SessionOptions sequences survive JSON serialization as tuples."""

    class Recorder:
        def __init__(self):
            self.seen = []

        async def __call__(self, io, user_turn, ctx):
            self.seen.append(ctx.options)
            await io.emit("result", {"stop_reason": "end_turn"})

    team = Recorder()

    async def scenario():
        cm, _server, port = await _start_server(team)
        client = WebSocketSession(f"ws://localhost:{port}")
        try:
            opts = SessionOptions(
                allowed_tools=("Read",),
                disallowed_tools=("Bash",),
                max_turns=5,
                permission_mode="plan",
            )
            h = await client.start(team="t", options=opts)
            await client.send(h.session_id, "hi")
            async for ev in client.events(h.session_id):
                if ev.type == "result":
                    break
            await client.close(h.session_id)
        finally:
            await client.shutdown()
            await cm.__aexit__(None, None, None)

    run_async(scenario())
    assert team.seen, "runner never invoked"
    got = team.seen[-1]
    assert got.allowed_tools == ("Read",)
    assert got.disallowed_tools == ("Bash",)
    assert got.max_turns == 5
    assert got.permission_mode == "plan"
