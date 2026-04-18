"""ClaudeCodeDispatcher — spawns `claude -p` as an async subprocess.

See spec §5.3.1. Uses the user's Claude subscription; no per-token billing.

Wire format: `claude -p` with `--output-format stream-json` produces
newline-delimited JSON events on stdout. We forward every parsed event to
the caller's event_sink and return a DispatchResult built from the final
`result` event.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import time
import uuid
from typing import Any

from .base import (
    AgentDefinition,
    DispatchCorrelation,
    DispatchError,
    DispatchResult,
    Dispatcher,
    EventSink,
)

DEFAULT_MODEL_MAP: dict[str, str] = {
    "high-reasoning": "claude-opus-4-6",
    "balanced": "claude-sonnet-4-6",
    "fast-cheap": "claude-haiku-4-5-20251001",
}


def _uuid_from_dispatch_id(dispatch_id: str) -> str:
    """Map a dispatch_id (e.g. "disp_a1b2c3d4") to a deterministic UUID
    string the Claude CLI will accept as --session-id. Using a UUID v5
    namespace keeps the mapping stable across replays while still being
    unique per dispatch."""
    namespace = uuid.NAMESPACE_OID
    return str(uuid.uuid5(namespace, dispatch_id))


class ClaudeCodeDispatcher(Dispatcher):
    def __init__(
        self,
        model_map: dict[str, str] | None = None,
        claude_bin: str | None = None,
    ):
        self._model_map = dict(DEFAULT_MODEL_MAP)
        if model_map:
            self._model_map.update(model_map)
        self._claude_bin = claude_bin or shutil.which("claude") or "claude"

    def resolve_model(self, logical_model: str) -> str:
        try:
            return self._model_map[logical_model]
        except KeyError as e:
            raise DispatchError(
                f"Unknown logical model: {logical_model!r}"
            ) from e

    async def dispatch(
        self,
        agent: AgentDefinition,
        prompt: str,
        logical_model: str,
        response_schema: dict | None,
        correlation: DispatchCorrelation,
        event_sink: EventSink,
        timeout_seconds: float = 300.0,
    ) -> DispatchResult:
        model = self.resolve_model(logical_model)
        agents_json = json.dumps(
            {
                agent.name: {
                    "prompt": agent.prompt,
                    "allowedTools": agent.allowed_tools,
                }
            }
        )
        argv = [
            self._claude_bin,
            "-p",
            prompt,
            "--agents",
            agents_json,
            "--output-format",
            "stream-json",
            # --output-format=stream-json with --print requires --verbose
            # (the CLI rejects the combination otherwise).
            "--verbose",
            "--include-partial-messages",
            "--include-hook-events",
            # Claude CLI --session-id must be unique per invocation — it's
            # the CLI's conversation identifier, not the conductor's. We
            # derive a valid UUID from the dispatch_id so parallel
            # dispatches within one conductor session don't collide.
            "--session-id",
            _uuid_from_dispatch_id(correlation.dispatch_id),
            "--model",
            model,
        ]
        if response_schema is not None:
            argv.extend(["--json-schema", json.dumps(response_schema)])

        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise DispatchError(f"claude binary not found: {self._claude_bin}") from e

        event_count = 0
        final_result: dict[str, Any] | None = None

        async def _drain_stdout() -> None:
            nonlocal event_count, final_result
            assert proc.stdout is not None
            async for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_count += 1
                await event_sink(evt)
                if evt.get("type") == "result" or evt.get("kind") == "result":
                    final_result = evt

        try:
            await asyncio.wait_for(
                asyncio.gather(_drain_stdout(), proc.wait()),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
            raise DispatchError(
                f"Dispatch for agent {agent.name!r} timed out "
                f"after {timeout_seconds}s"
            )

        duration_ms = int((time.monotonic() - start) * 1000)
        terminated_normally = proc.returncode == 0

        if final_result is None:
            stderr = (await proc.stderr.read()).decode("utf-8", errors="replace") if proc.stderr else ""
            raise DispatchError(
                f"Dispatch produced no final result event. "
                f"returncode={proc.returncode} stderr={stderr[:500]!r}"
            )

        response = _extract_response(final_result, response_schema)
        return DispatchResult(
            response=response,
            duration_ms=duration_ms,
            events=event_count,
            terminated_normally=terminated_normally,
            error=None if terminated_normally else f"exit {proc.returncode}",
        )


def _extract_response(
    final_event: dict[str, Any], response_schema: dict | None
) -> Any:
    """Pull the response payload from a `claude -p` result event.

    When `--json-schema` is passed, `claude -p` emits structured output
    on the result event; otherwise text content is returned. This function
    is intentionally forgiving about the exact field name to keep the
    walking skeleton decoupled from small CLI wire-format changes — we
    try the most likely keys in order and return the first match.
    """
    for key in ("structured_output", "json", "content", "result", "output"):
        if key in final_event:
            return final_event[key]
    return final_event
