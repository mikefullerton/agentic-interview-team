"""Stdio NDJSON transport.

Two halves:

* `serve_stdio(session, stdin, stdout)` — server loop. Reads newline-
  delimited JSON commands from `stdin`, calls the corresponding
  `TeamSession` method, and writes replies + async events to `stdout`.
* `StdioSession` — client-side `TeamSession` that spawns a subprocess
  running a `serve_stdio` loop and demultiplexes its NDJSON output back
  into per-session event queues.

Wire format (one JSON object per line, both directions):

  request: {"op": "start" | "send" | "answer" | "resume" | "close",
            "request_id": "<str>", ...op-specific fields...}
  reply:   {"kind": "ack", "request_id": "<str>", ...op-specific fields...}
           {"kind": "error", "request_id": "<str>", "message": "<str>"}
           {"kind": "event",
             "event": {"type", "session_id", "seq", "payload"}}

The framing only promises per-line atomicity; partial reads are the
stream reader's concern and are handled by `asyncio.StreamReader.readline()`.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import IO, Any

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
    """Rehydrate SessionOptions from JSON. Tuples serialize as lists, so
    we convert the sequence fields back before constructing."""
    return SessionOptions(
        allowed_tools=tuple(raw.get("allowed_tools", ())),
        disallowed_tools=tuple(raw.get("disallowed_tools", ())),
        max_turns=raw.get("max_turns"),
        permission_mode=raw.get("permission_mode", "default"),
    )


async def serve_stdio(
    session: TeamSession,
    stdin: asyncio.StreamReader,
    stdout: IO[bytes] | "asyncio.StreamWriter",
) -> None:
    """Drive `session` from NDJSON on `stdin`, emit NDJSON to `stdout`.

    Runs until stdin closes or an unrecoverable error occurs. `stdout`
    may be an `asyncio.StreamWriter` (subprocess pipes on some
    platforms) or a plain binary IO (subprocess stdout where the pipe
    transport isn't available, e.g. when the write pipe is a pty).
    Open sessions have a background forwarder task that pumps their
    event stream onto stdout as `{"kind": "event", ...}` lines.
    """
    forwarders: dict[str, asyncio.Task[None]] = {}
    write_lock = asyncio.Lock()
    is_stream_writer = hasattr(stdout, "drain") and hasattr(stdout, "write")

    async def write(obj: dict[str, Any]) -> None:
        line = (json.dumps(obj, separators=(",", ":")) + "\n").encode()
        async with write_lock:
            if is_stream_writer and hasattr(stdout, "drain"):
                stdout.write(line)  # type: ignore[union-attr]
                try:
                    await stdout.drain()  # type: ignore[union-attr]
                except (BrokenPipeError, ConnectionResetError):
                    raise
            else:
                try:
                    stdout.write(line)  # type: ignore[arg-type]
                    stdout.flush()  # type: ignore[union-attr]
                except (BrokenPipeError, ConnectionResetError):
                    raise

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

    while True:
        line = await stdin.readline()
        if not line:
            break
        try:
            cmd = json.loads(line.decode("utf-8"))
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

    for task in forwarders.values():
        task.cancel()


async def serve_from_streams() -> None:
    """Convenience entry point used by subprocess harnesses.

    Reads a JSON env var `AGENTIC_STDIO_BOOT` naming a dotted import
    path that returns a `TeamSession`; then runs `serve_stdio` against
    os.stdin / os.stdout.
    """
    import importlib

    boot = os.environ.get("AGENTIC_STDIO_BOOT")
    if boot is None:
        raise RuntimeError("AGENTIC_STDIO_BOOT not set")
    module_path, func_name = boot.rsplit(":", 1)
    mod = importlib.import_module(module_path)
    session: TeamSession = await getattr(mod, func_name)()

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    transport, stream_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(transport, stream_protocol, None, loop)

    try:
        await serve_stdio(session, reader, writer)
    finally:
        await session.close  # noqa: E501  (best-effort; impl-specific)


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


class StdioSession(TeamSession):
    """Client-side TeamSession that drives an NDJSON subprocess."""

    def __init__(self, cmd: list[str], env: dict[str, str] | None = None):
        self._cmd = cmd
        self._env = env
        self._proc: asyncio.subprocess.Process | None = None
        self._sessions: dict[str, _ClientSession] = {}
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._start_lock = asyncio.Lock()

    async def _ensure_started(self) -> None:
        async with self._start_lock:
            if self._proc is not None:
                return
            merged_env = os.environ.copy()
            if self._env:
                merged_env.update(self._env)
            self._proc = await asyncio.create_subprocess_exec(
                *self._cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env,
            )
            self._reader_task = asyncio.create_task(self._read_stdout())
            self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _read_stdout(self) -> None:
        assert self._proc is not None
        assert self._proc.stdout is not None
        try:
            async for raw in self._proc.stdout:
                try:
                    msg = json.loads(raw.decode("utf-8"))
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
            # Subprocess stdout closed — fail any outstanding requests
            # and terminate every session's event stream.
            for fut in list(self._pending.values()):
                if not fut.done():
                    fut.set_exception(
                        RuntimeError("stdio subprocess exited unexpectedly")
                    )
            self._pending.clear()
            for sess in self._sessions.values():
                if not sess.closed:
                    sess.closed = True
                    await sess.queue.put(None)

    async def _drain_stderr(self) -> None:
        assert self._proc is not None
        if self._proc.stderr is None:
            return
        async for _ in self._proc.stderr:
            pass

    async def _request(self, op: str, **fields: Any) -> dict[str, Any]:
        await self._ensure_started()
        assert self._proc is not None and self._proc.stdin is not None
        rid = uuid.uuid4().hex
        payload = {"op": op, "request_id": rid, **fields}
        fut: asyncio.Future[dict[str, Any]] = (
            asyncio.get_event_loop().create_future()
        )
        self._pending[rid] = fut
        self._proc.stdin.write(
            (json.dumps(payload, separators=(",", ":")) + "\n").encode()
        )
        try:
            await self._proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as exc:
            self._pending.pop(rid, None)
            raise RuntimeError("stdio subprocess stdin closed") from exc
        msg = await fut
        if msg.get("kind") == "error":
            raise RuntimeError(msg.get("message", "stdio op failed"))
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
            # Subprocess already gone — still tidy local state.
            pass
        sess = self._sessions.get(session_id)
        if sess is not None and not sess.closed:
            sess.closed = True
            await sess.queue.put(None)

    async def shutdown(self) -> None:
        """Terminate the subprocess and wait for reader tasks. Used by
        tests; hosts normally just let the process exit when they do."""
        if self._proc is None:
            return
        if self._proc.stdin is not None:
            try:
                self._proc.stdin.close()
            except Exception:
                pass
        try:
            await asyncio.wait_for(self._proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            self._proc.terminate()
            await self._proc.wait()
        if self._reader_task is not None:
            try:
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._reader_task.cancel()
        if self._stderr_task is not None:
            self._stderr_task.cancel()
