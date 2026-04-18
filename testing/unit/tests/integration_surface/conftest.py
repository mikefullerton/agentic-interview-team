"""Integration surface test fixtures.

`transport_factory` is parametrized over every available transport. Any
new transport (stdio, WebSocket, …) registers itself here so the full
`contract/` suite runs against it.
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.integration_surface import (  # noqa: E402
    Event,
    InProcessSession,
    SessionHandle,
    SessionOptions,
    StdioSession,
    TeamSession,
    WebSocketSession,
    serve_websocket,
)

from .fixtures.fake_team import FakeTeam  # noqa: E402

try:
    from websockets.asyncio.server import serve as _ws_serve  # noqa: E402
    _WEBSOCKETS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WEBSOCKETS_AVAILABLE = False


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


def _serialize_fake(fake: FakeTeam) -> dict:
    """Serialize a FakeTeam's scripted replies into JSON that the stdio
    harness reconstructs in the subprocess. Only the default
    (always-match) matcher is supported — tests that need custom
    matchers must stay in-process."""
    replies = []
    for r in fake._replies:
        replies.append(
            {
                "events": [list(ev) for ev in r.events],
                "ask": list(r.ask) if r.ask is not None else None,
                "after_answer": [list(ev) for ev in r.after_answer],
            }
        )
    return {"replies": replies}


_STDIO_ENTRY = (
    REPO_ROOT
    / "testing"
    / "unit"
    / "tests"
    / "integration_surface"
    / "fixtures"
    / "stdio_server.py"
)


def _stdio_factory(runner) -> TeamSession:
    if not isinstance(runner, FakeTeam):
        pytest.skip("stdio transport factory only supports FakeTeam scripts")
    script = json.dumps(_serialize_fake(runner))
    return StdioSession(
        cmd=[sys.executable, str(_STDIO_ENTRY)],
        env={"AGENTIC_FAKE_SCRIPT": script, "PYTHONUNBUFFERED": "1"},
    )


class _LocalWebSocketSession(TeamSession):
    """TeamSession that spins up an in-process WS server on first use.

    Test-only wrapper: contract tests receive a `TeamSession` and drive
    it synchronously, but a WebSocket server must run in the same event
    loop as the test. We defer both server startup and client connect
    until the first request lands, then delegate to `WebSocketSession`.
    """

    def __init__(self, runner: object):
        self._runner = runner
        self._client: WebSocketSession | None = None
        self._server: object | None = None
        self._server_cm: object | None = None
        self._lock = asyncio.Lock()

    async def _ensure(self) -> WebSocketSession:
        async with self._lock:
            if self._client is not None:
                return self._client
            server_session = InProcessSession(self._runner)

            async def handler(ws: object) -> None:
                await serve_websocket(server_session, ws)

            self._server_cm = _ws_serve(handler, "localhost", 0)
            self._server = await self._server_cm.__aenter__()  # type: ignore[union-attr]
            port = self._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
            self._client = WebSocketSession(f"ws://localhost:{port}")
            return self._client

    async def start(
        self,
        team: str,
        prompt: str | None = None,
        options: SessionOptions | None = None,
    ) -> SessionHandle:
        c = await self._ensure()
        return await c.start(team, prompt, options)

    async def send(self, session_id: str, user_turn: str) -> None:
        c = await self._ensure()
        await c.send(session_id, user_turn)

    def events(self, session_id: str) -> AsyncIterator[Event]:
        assert self._client is not None, "events() called before a start()"
        return self._client.events(session_id)

    async def answer(
        self, session_id: str, question_id: str, content: str
    ) -> None:
        c = await self._ensure()
        await c.answer(session_id, question_id, content)

    async def resume(self, session_id: str) -> SessionHandle:
        c = await self._ensure()
        return await c.resume(session_id)

    async def close(
        self, session_id: str, reason: str | None = None
    ) -> None:
        if self._client is None:
            return
        await self._client.close(session_id, reason)

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.shutdown()
        if self._server_cm is not None:
            await self._server_cm.__aexit__(None, None, None)  # type: ignore[union-attr]


def _websocket_factory(runner) -> TeamSession:
    if not _WEBSOCKETS_AVAILABLE:
        pytest.skip("websockets library not installed")
    return _LocalWebSocketSession(runner)


@pytest.fixture(params=["in_process", "stdio", "websocket"])
def transport_factory(request) -> Callable[[object], TeamSession]:
    """Returns a factory callable: (runner) -> TeamSession."""
    kind = request.param
    if kind == "in_process":
        return lambda runner: InProcessSession(runner)
    if kind == "stdio":
        return _stdio_factory
    if kind == "websocket":
        return _websocket_factory
    raise AssertionError(f"unknown transport: {kind}")


@pytest.fixture
def collect_events():
    """Helper: consume `events(session_id)` until a terminator.

    Accepts either a single event type ("result") or a sentinel function.
    """
    async def _collect(
        session: TeamSession,
        session_id: str,
        until_type: str = "result",
    ) -> list:
        out = []
        async for ev in session.events(session_id):
            out.append(ev)
            if ev.type == until_type:
                return out
        return out

    return _collect
