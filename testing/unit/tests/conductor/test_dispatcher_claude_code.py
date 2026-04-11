"""ClaudeCodeDispatcher tests — no real `claude` binary required.

Uses the fake Python binary at `testing/fixtures/fake_claude_bin.py` to
emulate `claude -p --output-format stream-json`. Each test writes a JSON
scenario file into tmp_path, points the dispatcher at the fake binary
via the `claude_bin` constructor arg, and sets FAKE_CLAUDE_SCRIPT in the
environment.

This exercises the subprocess lifecycle end-to-end:
- argv construction (including model mapping and --session-id)
- stream-json stdout parsing
- final result extraction
- timeout handling (SIGTERM then SIGKILL)
- non-zero exit → DispatchError carrying stderr
- missing binary → typed error
- bad lines skipped without breaking the drain loop
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from services.conductor.dispatcher import (
    AgentDefinition,
    DispatchCorrelation,
    DispatchError,
)
from services.conductor.dispatcher.claude_code import (
    ClaudeCodeDispatcher,
    DEFAULT_MODEL_MAP,
)


FAKE_BIN = (
    Path(__file__).resolve().parents[4]
    / "testing"
    / "fixtures"
    / "fake_claude_bin.py"
)


def _write_script(tmp_path: Path, script: dict[str, Any]) -> Path:
    path = tmp_path / "fake_script.json"
    path.write_text(json.dumps(script), encoding="utf-8")
    return path


def _corr() -> DispatchCorrelation:
    return DispatchCorrelation(
        session_id=uuid4(),
        team_id="t",
        agent_id="a",
        dispatch_id="d_1",
    )


def _agent() -> AgentDefinition:
    return AgentDefinition(name="a", prompt="you are a test agent")


def _run_dispatch(
    tmp_path: Path,
    script: dict[str, Any],
    *,
    timeout_seconds: float = 5.0,
    logical_model: str = "balanced",
    response_schema: dict | None = None,
    claude_bin: Path | None = None,
    argv_out: Path | None = None,
):
    script_path = _write_script(tmp_path, script)
    env_backup = dict(os.environ)
    # Use python3 explicitly so the shebang doesn't need to resolve.
    # Spawn the fake as `python3 fake_claude_bin.py ...` via a shim path.
    os.environ["FAKE_CLAUDE_SCRIPT"] = str(script_path)
    if argv_out is not None:
        os.environ["FAKE_CLAUDE_ARGV_OUT"] = str(argv_out)
    try:
        dispatcher = ClaudeCodeDispatcher(
            claude_bin=str(claude_bin or FAKE_BIN)
        )
        events: list[dict] = []

        async def sink(evt):
            events.append(evt)

        async def _t():
            return await dispatcher.dispatch(
                agent=_agent(),
                prompt="hi",
                logical_model=logical_model,
                response_schema=response_schema,
                correlation=_corr(),
                event_sink=sink,
                timeout_seconds=timeout_seconds,
            )

        result = asyncio.run(_t())
        return result, events
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_happy_path_returns_dispatch_result(tmp_path):
    script = {
        "events": [
            {"type": "progress", "text": "thinking"},
            {"type": "progress", "text": "more thinking"},
            {"type": "progress", "text": "almost done"},
            {
                "type": "result",
                "structured_output": {"candidates": ["Buddy", "Max"]},
            },
        ]
    }
    result, events = _run_dispatch(tmp_path, script)
    assert result.terminated_normally is True
    assert result.events == 4
    assert result.response == {"candidates": ["Buddy", "Max"]}
    assert [e.get("type") for e in events] == [
        "progress",
        "progress",
        "progress",
        "result",
    ]


def test_missing_result_event_raises(tmp_path):
    script = {
        "events": [
            {"type": "progress", "text": "no result coming"},
            {"type": "progress", "text": "still no result"},
        ]
    }
    with pytest.raises(DispatchError) as exc_info:
        _run_dispatch(tmp_path, script)
    assert "no final result event" in str(exc_info.value).lower()


def test_non_zero_exit_raises_with_stderr(tmp_path):
    script = {
        "events": [
            {"type": "progress", "text": "before crash"},
        ],
        "stderr": "boom: fake crash happened",
        "exit_code": 1,
    }
    with pytest.raises(DispatchError) as exc_info:
        _run_dispatch(tmp_path, script)
    msg = str(exc_info.value)
    assert "no final result event" in msg.lower()
    assert "boom" in msg


def test_timeout_kills_subprocess(tmp_path):
    script = {
        "events": [
            {"type": "result", "structured_output": {"ok": True}},
        ],
        # Delay the result event past our timeout.
        "sleep_before_result": 5.0,
    }
    with pytest.raises(DispatchError) as exc_info:
        _run_dispatch(tmp_path, script, timeout_seconds=0.5)
    assert "timed out" in str(exc_info.value).lower()


def test_bad_json_line_is_skipped(tmp_path):
    script = {
        "emit_bad_json_line": True,
        "events": [
            {"type": "progress", "text": "after bad line"},
            {"type": "result", "structured_output": {"x": 1}},
        ],
    }
    result, events = _run_dispatch(tmp_path, script)
    assert result.terminated_normally is True
    assert result.response == {"x": 1}
    # Bad line was skipped — only two parsed events.
    assert result.events == 2


def test_missing_binary_raises_typed_error(tmp_path):
    dispatcher = ClaudeCodeDispatcher(claude_bin="/nonexistent/claude-binary")

    async def sink(_):
        return None

    async def _t():
        await dispatcher.dispatch(
            agent=_agent(),
            prompt="hi",
            logical_model="balanced",
            response_schema=None,
            correlation=_corr(),
            event_sink=sink,
        )

    with pytest.raises(DispatchError) as exc_info:
        asyncio.run(_t())
    assert "claude binary not found" in str(exc_info.value)


def test_model_resolution_reaches_argv(tmp_path):
    """The fast-cheap logical model must reach argv as the haiku model ID."""
    argv_out = tmp_path / "argv.json"
    script = {
        "events": [
            {"type": "result", "structured_output": {"ok": True}},
        ]
    }
    _run_dispatch(
        tmp_path,
        script,
        logical_model="fast-cheap",
        argv_out=argv_out,
    )
    argv = json.loads(argv_out.read_text())
    assert "--model" in argv
    model = argv[argv.index("--model") + 1]
    assert model == DEFAULT_MODEL_MAP["fast-cheap"]


def test_session_id_reaches_argv(tmp_path):
    argv_out = tmp_path / "argv.json"
    script = {
        "events": [
            {"type": "result", "structured_output": {"ok": True}},
        ]
    }
    # Use a deterministic correlation so we can assert.
    correlation = DispatchCorrelation(
        session_id=uuid4(),
        team_id="t",
        agent_id="a",
        dispatch_id="d_1",
    )

    env_backup = dict(os.environ)
    os.environ["FAKE_CLAUDE_SCRIPT"] = str(_write_script(tmp_path, script))
    os.environ["FAKE_CLAUDE_ARGV_OUT"] = str(argv_out)
    try:
        dispatcher = ClaudeCodeDispatcher(claude_bin=str(FAKE_BIN))

        async def sink(_):
            return None

        async def _t():
            return await dispatcher.dispatch(
                agent=_agent(),
                prompt="hi",
                logical_model="balanced",
                response_schema=None,
                correlation=correlation,
                event_sink=sink,
            )

        asyncio.run(_t())
    finally:
        os.environ.clear()
        os.environ.update(env_backup)

    argv = json.loads(argv_out.read_text())
    assert "--session-id" in argv
    sid_in_argv = argv[argv.index("--session-id") + 1]
    assert sid_in_argv == str(correlation.session_id)


def test_unknown_logical_model_raises_before_spawn(tmp_path):
    dispatcher = ClaudeCodeDispatcher(claude_bin=str(FAKE_BIN))

    async def sink(_):
        return None

    async def _t():
        await dispatcher.dispatch(
            agent=_agent(),
            prompt="hi",
            logical_model="nonexistent-tier",
            response_schema=None,
            correlation=_corr(),
            event_sink=sink,
        )

    with pytest.raises(DispatchError) as exc_info:
        asyncio.run(_t())
    assert "nonexistent-tier" in str(exc_info.value)


def test_response_schema_is_passed_as_json_arg(tmp_path):
    argv_out = tmp_path / "argv.json"
    script = {
        "events": [
            {"type": "result", "structured_output": {"x": 1}},
        ]
    }
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    _run_dispatch(
        tmp_path,
        script,
        response_schema=schema,
        argv_out=argv_out,
    )
    argv = json.loads(argv_out.read_text())
    assert "--json-schema" in argv
    rendered = argv[argv.index("--json-schema") + 1]
    assert json.loads(rendered) == schema
