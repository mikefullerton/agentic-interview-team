"""Roll-call orchestrator — one session per role, bounded concurrency."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable

from services.integration_surface import Event, TeamSession

from .discovery import RoleRef


ROLL_CALL_PROMPT = (
    "You are participating in a roll-call. In one sentence, state: "
    "(a) your role, (b) the team you serve, (c) any readiness concerns."
)


@dataclass(frozen=True)
class RollCallError:
    kind: str
    message: str


@dataclass(frozen=True)
class RollCallResult:
    role: RoleRef
    response: str
    duration_ms: int
    error: RollCallError | None
    events: tuple[Event, ...] = ()


async def _ping_one(
    session: TeamSession,
    role: RoleRef,
    prompt: str,
    timeout: float,
) -> RollCallResult:
    start = time.monotonic()
    events: list[Event] = []
    response_parts: list[str] = []
    handle = None
    try:
        handle = await session.start(team=role.team)
        await session.send(handle.session_id, prompt)

        async def _consume() -> None:
            async for ev in session.events(handle.session_id):
                events.append(ev)
                if ev.type == "text":
                    text = ev.payload.get("text", "")
                    if text:
                        response_parts.append(text)
                if ev.type == "result":
                    return
                if ev.type == "error":
                    raise RuntimeError(
                        ev.payload.get("message", "error event")
                    )

        await asyncio.wait_for(_consume(), timeout=timeout)
        err: RollCallError | None = None
    except asyncio.TimeoutError:
        err = RollCallError(kind="timeout", message=f">{timeout}s")
    except Exception as exc:
        err = RollCallError(kind="error", message=str(exc))
    finally:
        if handle is not None:
            try:
                await session.close(handle.session_id)
            except Exception:
                pass

    return RollCallResult(
        role=role,
        response="".join(response_parts),
        duration_ms=int((time.monotonic() - start) * 1000),
        error=err,
        events=tuple(events),
    )


async def roll_call(
    session: TeamSession,
    roles: Iterable[RoleRef],
    *,
    prompt: str = ROLL_CALL_PROMPT,
    concurrency: int = 4,
    timeout: float = 30.0,
) -> list[RollCallResult]:
    """Ping every role once. Errors attach to the per-role result; the
    run as a whole always completes."""
    roles = list(roles)
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(r: RoleRef) -> RollCallResult:
        async with semaphore:
            return await _ping_one(session, r, prompt, timeout)

    return list(await asyncio.gather(*(_guarded(r) for r in roles)))
