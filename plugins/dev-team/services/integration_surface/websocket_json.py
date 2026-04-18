"""WebSocket transport.

Mirrors `stdio_ndjson.py`: same JSON message shapes, different framing.
WebSocket frames already preserve message boundaries so we drop the
newline delimiter.

Two halves:

* `serve_websocket(session, websocket)` — server handler. Accepts a
  `websockets.asyncio.server.ServerConnection` and drives `session` on
  it. One WS connection hosts many protocol sessions, demuxed by
  `session_id` the same way stdio does it.
* `WebSocketSession` — client-side `TeamSession` that connects to a
  `ws://` URL and routes incoming frames to per-session event queues.

Requires the `websockets` library (>= 12).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from .protocol import (
    Event,
    SessionHandle,
    SessionOptions,
    TeamSession,
)


# ---------------------------------------------------------------------------
# Server side
# ---------------------------------------------------------------------------


def _decode_options(raw: dict[str, Any]) -> SessionOptions:
    """Rehydrate a SessionOptions dict from JSON. JSON turns tuples into
    lists; this converts them back so the runner sees the same type the
    host built."""
    return SessionOptions(
        allowed_tools=tuple(raw.get("allowed_tools", ())),
        disallowed_tools=tuple(raw.get("disallowed_tools", ())),
        max_turns=raw.get("max_turns"),
        permission_mode=raw.get("permission_mode", "default"),
    )


async def serve_websocket(session: TeamSession, websocket: Any) -> None:
    """Drive `session` from JSON messages on `websocket`.

    `websocket` is a `websockets.asyncio.server.ServerConnection`. The
    function runs until the connection closes or an unrecoverable error
    occurs. Per-session event forwarders pump the session's event
    stream onto the socket as `{"kind": "event", ...}` messages.
    """
    forwarders: dict[str, asyncio.Task[None]] = {}
    write_lock = asyncio.Lock()

    async def write(obj: dict[str, Any]) -> None:
        line = json.dumps(obj, separators=(",", ":"))
        async with write_lock:
            await websocket.send(line)

    async def forward(session_id: str) -> None:
        try:
            async for ev in session.events(session_id):
                await write(
                    {
                        "kind": "event",
                        "event": {
                            "type": ev.type,
                            "session_id": ev.session_id,
                            "seq": ev.seq,
                            "payload": ev.payload,
                        },
                    }
                )
        except Exception as exc:
            await write(
                {
                    "kind": "error",
                    "request_id": None,
                    "message": f"forwarder for {session_id} crashed: {exc}",
                }
            )

    try:
        async for raw in websocket:
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
            try:
                cmd = json.loads(raw)
            except json.JSONDecodeError as exc:
                await write(
                    {
                        "kind": "error",
                        "request_id": None,
                        "message": f"invalid json: {exc}",
                    }
                )
                continue

            op = cmd.get("op")
            request_id = cmd.get("request_id")
            try:
                if op == "start":
                    options = (
                        _decode_options(cmd["options"])
                        if cmd.get("options")
                        else None
                    )
                    handle = await session.start(
                        team=cmd["team"],
                        prompt=cmd.get("prompt"),
                        options=options,
                    )
                    forwarders[handle.session_id] = asyncio.create_task(
                        forward(handle.session_id)
                    )
                    await write(
                        {
                            "kind": "ack",
                            "request_id": request_id,
                            "session_id": handle.session_id,
                            "team": handle.team,
                        }
                    )
                elif op == "send":
                    await session.send(cmd["session_id"], cmd["user_turn"])
                    await write({"kind": "ack", "request_id": request_id})
                elif op == "answer":
                    await session.answer(
                        cmd["session_id"],
                        cmd["question_id"],
                        cmd["content"],
                    )
                    await write({"kind": "ack", "request_id": request_id})
                elif op == "resume":
                    handle = await session.resume(cmd["session_id"])
                    if handle.session_id not in forwarders:
                        forwarders[handle.session_id] = asyncio.create_task(
                            forward(handle.session_id)
                        )
                    await write(
                        {
                            "kind": "ack",
                            "request_id": request_id,
                            "session_id": handle.session_id,
                            "team": handle.team,
                        }
                    )
                elif op == "close":
                    await session.close(
                        cmd["session_id"], reason=cmd.get("reason")
                    )
                    task = forwarders.pop(cmd["session_id"], None)
                    if task is not None:
                        try:
                            await asyncio.wait_for(task, timeout=1.0)
                        except asyncio.TimeoutError:
                            task.cancel()
                    await write({"kind": "ack", "request_id": request_id})
                else:
                    await write(
                        {
                            "kind": "error",
                            "request_id": request_id,
                            "message": f"unknown op: {op!r}",
                        }
                    )
            except Exception as exc:
                await write(
                    {
                        "kind": "error",
                        "request_id": request_id,
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                )
    finally:
        for task in forwarders.values():
            task.cancel()


# ---------------------------------------------------------------------------
# Client side
# ---------------------------------------------------------------------------


@dataclass
class _ClientSession:
    team: str
    queue: "asyncio.Queue[Event | None]" = field(
        default_factory=lambda: asyncio.Queue()
    )
    closed: bool = False


class WebSocketSession(TeamSession):
    """Client-side TeamSession that talks to a `serve_websocket` server.

    One connection hosts many protocol sessions; session IDs coming back
    from `start` route incoming event frames to per-session queues.
    """

    def __init__(self, url: str):
        self._url = url
        self._ws: Any = None
        self._sessions: dict[str, _ClientSession] = {}
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._start_lock = asyncio.Lock()

    async def _ensure_started(self) -> None:
        async with self._start_lock:
            if self._ws is not None:
                return
            from websockets.asyncio.client import connect

            self._ws = await connect(self._url)
            self._reader_task = asyncio.create_task(self._read_socket())

    async def _read_socket(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode("utf-8")
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                kind = msg.get("kind")
                if kind in {"ack", "error"}:
                    rid = msg.get("request_id")
                    fut = self._pending.pop(rid, None) if rid else None
                    if fut is not None and not fut.done():
                        fut.set_result(msg)
                elif kind == "event":
                    ev = msg["event"]
                    sid = ev["session_id"]
                    sess = self._sessions.get(sid)
                    if sess is None:
                        continue
                    await sess.queue.put(
                        Event(
                            type=ev["type"],
                            session_id=sid,
                            seq=ev["seq"],
                            payload=ev.get("payload", {}),
                        )
                    )
        finally:
            for fut in list(self._pending.values()):
                if not fut.done():
                    fut.set_exception(
                        RuntimeError("websocket connection closed")
                    )
            self._pending.clear()
            for sess in self._sessions.values():
                if not sess.closed:
                    sess.closed = True
                    await sess.queue.put(None)

    async def _request(self, op: str, **fields: Any) -> dict[str, Any]:
        await self._ensure_started()
        assert self._ws is not None
        rid = uuid.uuid4().hex
        payload = {"op": op, "request_id": rid, **fields}
        fut: asyncio.Future[dict[str, Any]] = (
            asyncio.get_event_loop().create_future()
        )
        self._pending[rid] = fut
        try:
            await self._ws.send(json.dumps(payload, separators=(",", ":")))
        except Exception as exc:
            self._pending.pop(rid, None)
            raise RuntimeError(f"websocket send failed: {exc}") from exc
        msg = await fut
        if msg.get("kind") == "error":
            raise RuntimeError(msg.get("message", "websocket op failed"))
        return msg

    async def start(
        self,
        team: str,
        prompt: str | None = None,
        options: SessionOptions | None = None,
    ) -> SessionHandle:
        fields: dict[str, Any] = {"team": team}
        if prompt is not None:
            fields["prompt"] = prompt
        if options is not None:
            fields["options"] = {
                "allowed_tools": list(options.allowed_tools),
                "disallowed_tools": list(options.disallowed_tools),
                "max_turns": options.max_turns,
                "permission_mode": options.permission_mode,
            }
        reply = await self._request("start", **fields)
        sid = reply["session_id"]
        self._sessions[sid] = _ClientSession(team=reply["team"])
        return SessionHandle(session_id=sid, team=reply["team"])

    async def send(self, session_id: str, user_turn: str) -> None:
        await self._request(
            "send", session_id=session_id, user_turn=user_turn
        )

    async def events(self, session_id: str) -> AsyncIterator[Event]:
        sess = self._sessions.get(session_id)
        if sess is None:
            raise KeyError(f"unknown session: {session_id}")
        while True:
            item = await sess.queue.get()
            if item is None:
                return
            yield item

    async def answer(
        self, session_id: str, question_id: str, content: str
    ) -> None:
        await self._request(
            "answer",
            session_id=session_id,
            question_id=question_id,
            content=content,
        )

    async def resume(self, session_id: str) -> SessionHandle:
        reply = await self._request("resume", session_id=session_id)
        return SessionHandle(
            session_id=reply["session_id"], team=reply["team"]
        )

    async def close(
        self, session_id: str, reason: str | None = None
    ) -> None:
        try:
            await self._request(
                "close", session_id=session_id, reason=reason
            )
        except RuntimeError:
            pass
        sess = self._sessions.get(session_id)
        if sess is not None and not sess.closed:
            sess.closed = True
            await sess.queue.put(None)

    async def shutdown(self) -> None:
        """Close the websocket and drain reader tasks."""
        if self._ws is None:
            return
        try:
            await self._ws.close()
        except Exception:
            pass
        if self._reader_task is not None:
            try:
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._reader_task.cancel()
