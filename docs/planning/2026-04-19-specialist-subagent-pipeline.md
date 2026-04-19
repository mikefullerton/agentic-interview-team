# Specialist Subagent Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the specialist a `claude -p` subprocess that dispatches two generic subagents (`speciality-worker`, `speciality-verifier`) via the Task tool. Conductor records one parent `dispatch` per plan_node and child `dispatch` rows per subagent call, grouped into `attempt` rows declared by the specialist's final structured output.

**Architecture:** Additive — new `dispatch`/`attempt` tables + `parent_dispatch_id` column. New `SpecialistDispatcher` composes an existing `ClaudeCodeDispatcher` call with stream-json parsing for child `tool_use` events. `generic_realizer.py` switches to the specialist path. Two subagent markdown files carry the generic worker/verifier system prompts.

**Tech Stack:** Python 3.10+, stdlib sqlite3/asyncio, pytest. Subagent definitions authored as `.claude/agents/*.md`-style markdown with YAML frontmatter, loaded at dispatch time.

**Context:** Design notes at `docs/research/specialist-subagent-pipeline.md`.

---

## Scope Notes

**In scope:**
- Live-schema additions: `dispatch`, `attempt`, with `parent_dispatch_id` on `dispatch`.
- Arbitrator API: `create_dispatch`, `close_dispatch`, `create_attempt`.
- `SpecialistDispatcher` class — composes specialist prompt from `team.json`, spawns `claude -p` with `--agents` carrying the two generic subagents, parses stream-json for child `tool_use` events, reads attempts from final result.
- Two subagent files: `plugins/dev-team/subagents/speciality-worker.md`, `plugins/dev-team/subagents/speciality-verifier.md`.
- `generic_realizer.py` switched to use `SpecialistDispatcher`.
- Mock-path wiring so existing tests still run without real LLM calls.

**Out of scope (follow-up plans):**
- Real LLM integration tests (no API key in CI).
- Parallel speciality dispatch within one specialist subprocess (sequential for skeleton).
- Retry/backoff inside the specialist (first-attempt-only for skeleton; verdict still recorded).
- Exploratory_prompts surfacing.

---

## Task 1: Add `dispatch` + `attempt` tables to live schema

**Files:**
- Modify: `plugins/dev-team/services/conductor/arbitrator/backends/schema.sql`
- Create: `testing/unit/tests/conductor/contract/test_dispatch_schema.py`

- [ ] **Step 1: Write the failing schema test**

`testing/unit/tests/conductor/contract/test_dispatch_schema.py`:

```python
"""Live conductor schema carries dispatch + attempt tables with parent_dispatch_id."""
from __future__ import annotations


def test_dispatch_table_exists_with_parent_column(sqlite_conn):
    cols = {
        row[1] for row in sqlite_conn.execute(
            "PRAGMA table_info(dispatch)"
        ).fetchall()
    }
    assert {
        "dispatch_id", "session_id", "team_id", "plan_node_id",
        "parent_dispatch_id", "agent_kind", "agent_name",
        "logical_model", "concrete_model", "status",
        "start_date", "end_date",
    } <= cols


def test_attempt_table_exists(sqlite_conn):
    cols = {
        row[1] for row in sqlite_conn.execute(
            "PRAGMA table_info(attempt)"
        ).fetchall()
    }
    assert {
        "attempt_id", "result_id", "session_id",
        "attempt_kind", "attempt_number",
        "worker_dispatch_id", "verifier_dispatch_id", "verdict",
        "start_date", "end_date",
    } <= cols


def test_parent_dispatch_fk_rejects_unknown(sqlite_conn, iso_now, seed_session):
    import sqlite3
    sess = seed_session(session_id="s-d")
    with __import__("pytest").raises(sqlite3.IntegrityError):
        sqlite_conn.execute(
            "INSERT INTO dispatch "
            "(dispatch_id, session_id, team_id, parent_dispatch_id, "
            " agent_kind, agent_name, logical_model, status, start_date) "
            "VALUES ('d1', ?, 't1', 'ghost', 'worker', 'w', 'balanced', "
            " 'running', ?)",
            (sess, iso_now),
        )


def test_attempt_fk_requires_real_worker_dispatch(sqlite_conn, iso_now, seed_session):
    import sqlite3
    sess = seed_session(session_id="s-a")
    sqlite_conn.execute(
        "INSERT INTO result "
        "(result_id, session_id, team_id, specialist_id, passed, "
        " summary_json, creation_date) "
        "VALUES ('r1', ?, 't1', 'sp', 1, '{}', ?)",
        (sess, iso_now),
    )
    with __import__("pytest").raises(sqlite3.IntegrityError):
        sqlite_conn.execute(
            "INSERT INTO attempt "
            "(attempt_id, result_id, session_id, attempt_kind, "
            " attempt_number, worker_dispatch_id, start_date) "
            "VALUES ('a1', 'r1', ?, 'speciality', 1, 'ghost-w', ?)",
            (sess, iso_now),
        )
```

- [ ] **Step 2: Run it — expect FAIL (tables don't exist yet)**

Run: `pytest testing/unit/tests/conductor/contract/test_dispatch_schema.py -v`
Expected: 4 errors — `no such table: dispatch`.

- [ ] **Step 3: Add the tables**

Append to `plugins/dev-team/services/conductor/arbitrator/backends/schema.sql`:

```sql

-- ---------------------------------------------------------------------------
-- Dispatch log: one row per `claude -p` invocation (specialist) and per
-- subagent Task call (worker, verifier). Children point at their parent
-- via parent_dispatch_id so the specialist call is the root of a tree.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dispatch (
    dispatch_id         TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    plan_node_id        TEXT,
    parent_dispatch_id  TEXT,                      -- NULL = top-level (specialist)
    agent_kind          TEXT NOT NULL,             -- specialist|worker|verifier
    agent_name          TEXT NOT NULL,
    logical_model       TEXT NOT NULL,
    concrete_model      TEXT,
    status              TEXT NOT NULL,             -- running|completed|failed|timeout
    start_date          TEXT NOT NULL,
    end_date            TEXT,
    FOREIGN KEY (session_id)         REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id)       REFERENCES plan_node(node_id),
    FOREIGN KEY (parent_dispatch_id) REFERENCES dispatch(dispatch_id)
);
CREATE INDEX IF NOT EXISTS idx_dispatch_parent
    ON dispatch(parent_dispatch_id);
CREATE INDEX IF NOT EXISTS idx_dispatch_plan_node
    ON dispatch(plan_node_id);

-- ---------------------------------------------------------------------------
-- Attempt: groups a worker dispatch with its (optional) verifier dispatch
-- into one verdict-bearing unit of work. Declared by the specialist at the
-- end of its run.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS attempt (
    attempt_id              TEXT PRIMARY KEY,
    result_id               TEXT NOT NULL,
    session_id              TEXT NOT NULL,
    attempt_kind            TEXT NOT NULL,         -- speciality|consultation|...
    attempt_number          INTEGER NOT NULL,
    worker_dispatch_id      TEXT NOT NULL,
    verifier_dispatch_id    TEXT,
    verdict                 TEXT,                  -- pass|fail|skipped
    start_date              TEXT NOT NULL,
    end_date                TEXT,
    UNIQUE (result_id, attempt_kind, attempt_number),
    FOREIGN KEY (result_id)            REFERENCES result(result_id),
    FOREIGN KEY (session_id)           REFERENCES session(session_id),
    FOREIGN KEY (worker_dispatch_id)   REFERENCES dispatch(dispatch_id),
    FOREIGN KEY (verifier_dispatch_id) REFERENCES dispatch(dispatch_id)
);
CREATE INDEX IF NOT EXISTS idx_attempt_result
    ON attempt(result_id);
```

- [ ] **Step 4: Run test — expect PASS**

Run: `pytest testing/unit/tests/conductor/contract/test_dispatch_schema.py -v`
Expected: 4 passed.

- [ ] **Step 5: Verify schema_lint still passes**

Run: `pytest testing/unit/tests/conductor/contract/test_schema_conforms.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-team/services/conductor/arbitrator/backends/schema.sql \
        testing/unit/tests/conductor/contract/test_dispatch_schema.py
git commit -m "feat(arbitrator): dispatch + attempt tables with parent_dispatch_id"
git push
```

---

## Task 2: Arbitrator API for dispatch + attempt records

**Files:**
- Modify: `plugins/dev-team/services/conductor/arbitrator/api.py`
- Create: `testing/unit/tests/conductor/contract/test_dispatch_api.py`

- [ ] **Step 1: Write failing API test**

`testing/unit/tests/conductor/contract/test_dispatch_api.py`:

```python
"""Arbitrator create_dispatch/close_dispatch/create_attempt round-trip."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_create_dispatch_writes_row(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    d = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="platform-database",
        logical_model="balanced",
    ))
    assert d["dispatch_id"]
    assert d["status"] == "running"
    assert d["parent_dispatch_id"] is None


def test_child_dispatch_links_to_parent(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    parent = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="platform-database",
        logical_model="balanced",
    ))
    child = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="worker", agent_name="speciality-worker",
        logical_model="balanced",
        parent_dispatch_id=parent["dispatch_id"],
    ))
    assert child["parent_dispatch_id"] == parent["dispatch_id"]


def test_close_dispatch_sets_status_and_end(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    d = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="sp", logical_model="balanced",
    ))
    closed = run_async(arb.close_dispatch(
        d["dispatch_id"], status="completed", concrete_model="claude-sonnet-4-6",
    ))
    assert closed["status"] == "completed"
    assert closed["end_date"] is not None
    assert closed["concrete_model"] == "claude-sonnet-4-6"


def test_create_attempt_links_worker_and_verifier(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    result = run_async(arb.create_result(
        session_id=session_id, team_id="t",
        specialist_id="platform-database", passed=True, summary={},
    ))
    w = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="worker", agent_name="speciality-worker",
        logical_model="balanced",
    ))
    v = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="verifier", agent_name="speciality-verifier",
        logical_model="balanced",
    ))
    att = run_async(arb.create_attempt(
        result_id=result.result_id, session_id=session_id,
        attempt_kind="speciality", attempt_number=1,
        worker_dispatch_id=w["dispatch_id"],
        verifier_dispatch_id=v["dispatch_id"],
        verdict="pass",
    ))
    assert att["attempt_id"]
    assert att["verdict"] == "pass"
    assert att["worker_dispatch_id"] == w["dispatch_id"]
```

- [ ] **Step 2: Run it — expect FAIL (method doesn't exist)**

Run: `pytest testing/unit/tests/conductor/contract/test_dispatch_api.py -v`
Expected: AttributeError on `arb.create_dispatch`.

- [ ] **Step 3: Add the API methods**

In `plugins/dev-team/services/conductor/arbitrator/api.py`, add methods to the `Arbitrator` class (after `create_result`):

```python
    async def create_dispatch(
        self,
        *,
        session_id,
        team_id: str,
        agent_kind: str,
        agent_name: str,
        logical_model: str,
        plan_node_id: str | None = None,
        parent_dispatch_id: str | None = None,
        concrete_model: str | None = None,
    ) -> dict:
        dispatch_id = f"disp_{uuid.uuid4().hex[:12]}"
        now = _iso_now()
        row = {
            "dispatch_id": dispatch_id,
            "session_id": str(session_id),
            "team_id": team_id,
            "plan_node_id": plan_node_id,
            "parent_dispatch_id": parent_dispatch_id,
            "agent_kind": agent_kind,
            "agent_name": agent_name,
            "logical_model": logical_model,
            "concrete_model": concrete_model,
            "status": "running",
            "start_date": now,
            "end_date": None,
        }
        await self._storage.insert("dispatch", row)
        return row

    async def close_dispatch(
        self,
        dispatch_id: str,
        *,
        status: str,
        concrete_model: str | None = None,
    ) -> dict:
        now = _iso_now()
        patch: dict = {"status": status, "end_date": now}
        if concrete_model is not None:
            patch["concrete_model"] = concrete_model
        await self._storage.update(
            "dispatch", where={"dispatch_id": dispatch_id}, values=patch,
        )
        row = await self._storage.fetch_one(
            "dispatch", {"dispatch_id": dispatch_id},
        )
        return row

    async def create_attempt(
        self,
        *,
        result_id: str,
        session_id,
        attempt_kind: str,
        attempt_number: int,
        worker_dispatch_id: str,
        verifier_dispatch_id: str | None = None,
        verdict: str | None = None,
    ) -> dict:
        attempt_id = f"att_{uuid.uuid4().hex[:12]}"
        now = _iso_now()
        row = {
            "attempt_id": attempt_id,
            "result_id": result_id,
            "session_id": str(session_id),
            "attempt_kind": attempt_kind,
            "attempt_number": attempt_number,
            "worker_dispatch_id": worker_dispatch_id,
            "verifier_dispatch_id": verifier_dispatch_id,
            "verdict": verdict,
            "start_date": now,
            "end_date": now if verdict is not None else None,
        }
        await self._storage.insert("attempt", row)
        return row
```

Check the file head for `uuid` and `_iso_now` imports — both should already exist (used by `create_result`). If either is missing, add `import uuid` and whatever the helper is called (grep for one usage in the same file).

- [ ] **Step 4: Run test — expect PASS**

Run: `pytest testing/unit/tests/conductor/contract/test_dispatch_api.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-team/services/conductor/arbitrator/api.py \
        testing/unit/tests/conductor/contract/test_dispatch_api.py
git commit -m "feat(arbitrator): create_dispatch/close_dispatch/create_attempt"
git push
```

---

## Task 3: Generic subagent definitions (worker + verifier)

**Files:**
- Create: `plugins/dev-team/subagents/speciality-worker.md`
- Create: `plugins/dev-team/subagents/speciality-verifier.md`
- Create: `plugins/dev-team/services/conductor/subagents.py`
- Create: `testing/unit/tests/conductor/test_subagent_loader.py`

- [ ] **Step 1: Write failing loader test**

`testing/unit/tests/conductor/test_subagent_loader.py`:

```python
"""Subagent loader returns one AgentDefinition per markdown file."""
from __future__ import annotations

from services.conductor.subagents import load_generic_subagents


def test_loader_returns_worker_and_verifier():
    subs = load_generic_subagents()
    names = {s.name for s in subs}
    assert names == {"speciality-worker", "speciality-verifier"}


def test_worker_prompt_mentions_focus_and_structured_output():
    subs = {s.name: s for s in load_generic_subagents()}
    body = subs["speciality-worker"].prompt
    assert "focus" in body.lower()
    assert "structured" in body.lower() or "json" in body.lower()


def test_verifier_prompt_asks_for_verdict():
    subs = {s.name: s for s in load_generic_subagents()}
    body = subs["speciality-verifier"].prompt
    assert "verdict" in body.lower()
```

- [ ] **Step 2: Run it — expect FAIL (module not yet)**

Run: `pytest testing/unit/tests/conductor/test_subagent_loader.py -v`
Expected: ModuleNotFoundError on `services.conductor.subagents`.

- [ ] **Step 3: Write the two subagent files**

`plugins/dev-team/subagents/speciality-worker.md`:

```markdown
---
name: speciality-worker
description: Execute one unit of speciality work given focus prompt and upstream context.
tools:
  - Read
  - Glob
  - Grep
---

You are a speciality worker. Your parent specialist has given you a
focus prompt, any upstream context, and a structured-output schema.

Do the work. Return a single JSON object matching the requested schema.
Do not add prose outside the JSON.
```

`plugins/dev-team/subagents/speciality-verifier.md`:

```markdown
---
name: speciality-verifier
description: Verify a worker's output against the speciality's verify criteria.
tools:
  - Read
  - Glob
  - Grep
---

You are a speciality verifier. Your parent specialist has given you
(1) the worker's output and (2) the verify criteria for this speciality.

Return a single JSON object:

```json
{"verdict": "pass" | "fail", "reason": "<one sentence>"}
```

Do not add prose outside the JSON.
```

- [ ] **Step 4: Write the loader**

`plugins/dev-team/services/conductor/subagents.py`:

```python
"""Load generic speciality subagent definitions from disk.

The parent specialist dispatches these via the Task tool. Topic-specific
content (worker_focus, verify criteria) flows in as Task input at call
time — the subagent prompts stay generic.
"""
from __future__ import annotations

from pathlib import Path

from .dispatcher import AgentDefinition
from .team_loader import _parse_frontmatter

SUBAGENT_DIR = Path(__file__).resolve().parents[2] / "subagents"


def load_generic_subagents() -> list[AgentDefinition]:
    defs: list[AgentDefinition] = []
    for md in sorted(SUBAGENT_DIR.glob("*.md")):
        text = md.read_text()
        fm, body = _parse_frontmatter(text)
        name = fm.get("name") or md.stem
        tools_raw = fm.get("tools", "")
        tools = [t.strip(" -") for t in tools_raw.splitlines() if t.strip(" -")] \
            if "\n" in tools_raw else \
            [t.strip() for t in tools_raw.split(",") if t.strip()]
        defs.append(AgentDefinition(
            name=name, prompt=body.strip(),
            allowed_tools=tools,
        ))
    return defs
```

Note: `_parse_frontmatter` only handles flat key/value pairs. List-valued frontmatter (`tools:` with dash-bullets) gets the raw text — the loader above handles both forms defensively. If the test still fails on tool parsing, widen `_parse_frontmatter` to pass the raw block through unchanged and extend the loader's list splitter.

- [ ] **Step 5: Run test — expect PASS**

Run: `pytest testing/unit/tests/conductor/test_subagent_loader.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-team/subagents/ \
        plugins/dev-team/services/conductor/subagents.py \
        testing/unit/tests/conductor/test_subagent_loader.py
git commit -m "feat(conductor): generic speciality-worker/verifier subagents"
git push
```

---

## Task 4: Stream-json parser for child `tool_use` events

**Files:**
- Create: `plugins/dev-team/services/conductor/dispatcher/stream_parser.py`
- Create: `testing/unit/tests/conductor/test_stream_parser.py`

- [ ] **Step 1: Write failing parser test**

`testing/unit/tests/conductor/test_stream_parser.py`:

```python
"""Parser pulls Task-tool invocations out of a stream-json event sequence."""
from __future__ import annotations

from services.conductor.dispatcher.stream_parser import SubagentStreamParser


def test_parser_emits_start_and_end_for_each_task_call():
    parser = SubagentStreamParser()
    events = [
        {"type": "tool_use", "id": "tu1", "name": "Task",
         "input": {"subagent_type": "speciality-worker",
                   "description": "work",
                   "prompt": "do stuff"}},
        {"type": "tool_result", "tool_use_id": "tu1",
         "content": [{"type": "text", "text": '{"output": "ok"}'}]},
        {"type": "tool_use", "id": "tu2", "name": "Task",
         "input": {"subagent_type": "speciality-verifier",
                   "description": "verify",
                   "prompt": "check"}},
        {"type": "tool_result", "tool_use_id": "tu2",
         "content": [{"type": "text",
                      "text": '{"verdict": "pass"}'}]},
    ]
    starts, ends = [], []
    for e in events:
        out = parser.ingest(e)
        starts.extend(out.starts)
        ends.extend(out.ends)

    assert [s.subagent_name for s in starts] == [
        "speciality-worker", "speciality-verifier",
    ]
    assert [e.tool_use_id for e in ends] == ["tu1", "tu2"]


def test_parser_ignores_non_task_tools():
    parser = SubagentStreamParser()
    out = parser.ingest({"type": "tool_use", "id": "x", "name": "Read",
                         "input": {"file_path": "/tmp/foo"}})
    assert out.starts == []
    assert out.ends == []


def test_tool_result_without_matching_start_is_dropped():
    parser = SubagentStreamParser()
    out = parser.ingest({"type": "tool_result", "tool_use_id": "ghost",
                         "content": []})
    assert out.ends == []
```

- [ ] **Step 2: Run it — expect FAIL (module missing)**

Run: `pytest testing/unit/tests/conductor/test_stream_parser.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement the parser**

`plugins/dev-team/services/conductor/dispatcher/stream_parser.py`:

```python
"""Parse `claude -p` stream-json for subagent Task invocations.

The specialist's stream emits Anthropic-API-style tool_use / tool_result
events. When name == "Task", the payload represents a Task-tool
subagent invocation. This parser tracks those events so the caller can
open a child `dispatch` row on start and close it on result.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubagentStart:
    tool_use_id: str
    subagent_name: str
    description: str
    prompt: str


@dataclass
class SubagentEnd:
    tool_use_id: str
    output_text: str


@dataclass
class ParseStep:
    starts: list[SubagentStart] = field(default_factory=list)
    ends: list[SubagentEnd] = field(default_factory=list)


class SubagentStreamParser:
    def __init__(self) -> None:
        self._open: dict[str, SubagentStart] = {}

    def ingest(self, event: dict) -> ParseStep:
        step = ParseStep()
        etype = event.get("type")
        if etype == "tool_use" and event.get("name") == "Task":
            payload = event.get("input") or {}
            start = SubagentStart(
                tool_use_id=event.get("id", ""),
                subagent_name=payload.get("subagent_type", ""),
                description=payload.get("description", ""),
                prompt=payload.get("prompt", ""),
            )
            self._open[start.tool_use_id] = start
            step.starts.append(start)
        elif etype == "tool_result":
            tu_id = event.get("tool_use_id", "")
            if tu_id in self._open:
                text = _extract_text(event.get("content"))
                step.ends.append(SubagentEnd(tool_use_id=tu_id, output_text=text))
                self._open.pop(tu_id, None)
        return step


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(part.get("text", ""))
        return "".join(chunks)
    return ""
```

- [ ] **Step 4: Run test — expect PASS**

Run: `pytest testing/unit/tests/conductor/test_stream_parser.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-team/services/conductor/dispatcher/stream_parser.py \
        testing/unit/tests/conductor/test_stream_parser.py
git commit -m "feat(dispatcher): subagent stream-json parser"
git push
```

---

## Task 5: `SpecialistDispatcher` — composes claude -p call + stream parsing

**Files:**
- Create: `plugins/dev-team/services/conductor/dispatcher/specialist.py`
- Modify: `plugins/dev-team/services/conductor/dispatcher/__init__.py`
- Create: `testing/unit/tests/conductor/test_specialist_dispatcher.py`

- [ ] **Step 1: Write failing test using MockDispatcher under the hood**

`testing/unit/tests/conductor/test_specialist_dispatcher.py`:

```python
"""SpecialistDispatcher drives a child dispatcher through one claude -p call,
opening child dispatch rows for each Task subagent invocation in the stream."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.dispatcher.specialist import SpecialistDispatcher
from services.conductor.dispatcher.mock import MockDispatcher


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_specialist_dispatcher_records_parent_and_child_dispatches(
    arb, run_async, session_id,
):
    run_async(arb.open_session(session_id, initial_team_id="t"))

    # MockDispatcher emits a scripted stream-json sequence for one Task call
    # (worker) and then a final structured result declaring one attempt.
    inner = MockDispatcher()

    # Mock the underlying dispatch: scripted event sink + final response.
    async def fake_dispatch(agent, prompt, logical_model, response_schema,
                            correlation, event_sink, timeout_seconds=300.0):
        await event_sink({
            "type": "tool_use", "id": "tu1", "name": "Task",
            "input": {"subagent_type": "speciality-worker",
                      "description": "work", "prompt": "p"},
        })
        await event_sink({
            "type": "tool_result", "tool_use_id": "tu1",
            "content": [{"type": "text", "text": '{"output": "ok"}'}],
        })
        from services.conductor.dispatcher.base import DispatchResult
        return DispatchResult(
            response={
                "result": {"output": "ok"},
                "attempts": [{
                    "worker_tool_use_id": "tu1",
                    "verdict": "pass",
                }],
            },
            duration_ms=1, events=2, terminated_normally=True,
        )
    inner.dispatch = fake_dispatch  # type: ignore[assignment]

    sd = SpecialistDispatcher(inner=inner, arbitrator=arb)
    out = run_async(sd.run_specialist(
        session_id=session_id, team_id="t",
        plan_node_id="n1",
        specialist_name="platform-database",
        specialist_prompt="You are the database specialist...",
        worker_focus="Review indexes.",
        verify_criteria="Query plan uses them.",
        logical_model="balanced",
        subagent_defs=[],  # empty for mock path; real path loads from disk
    ))

    rows = run_async(arb._storage.fetch_all("dispatch"))
    kinds = sorted(r["agent_kind"] for r in rows)
    assert kinds == ["specialist", "worker"]
    parent = next(r for r in rows if r["agent_kind"] == "specialist")
    child  = next(r for r in rows if r["agent_kind"] == "worker")
    assert child["parent_dispatch_id"] == parent["dispatch_id"]

    attempts = run_async(arb._storage.fetch_all("attempt"))
    assert len(attempts) == 1
    assert attempts[0]["verdict"] == "pass"
    assert attempts[0]["worker_dispatch_id"] == child["dispatch_id"]

    assert out["response"]["result"]["output"] == "ok"
```

- [ ] **Step 2: Run it — expect FAIL (module missing)**

Run: `pytest testing/unit/tests/conductor/test_specialist_dispatcher.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement SpecialistDispatcher**

`plugins/dev-team/services/conductor/dispatcher/specialist.py`:

```python
"""SpecialistDispatcher — one plan_node → one `claude -p` subprocess for the
specialist, with worker/verifier subagents invoked internally via the Task tool.

This class wraps an inner Dispatcher (real or mock) and translates its
stream of events into child `dispatch` rows. The specialist's final
structured output is expected to include an `attempts` list that groups
child dispatches into worker↔verifier pairs with verdicts.
"""
from __future__ import annotations

import uuid
from typing import Any

from ..arbitrator import Arbitrator
from .base import (
    AgentDefinition,
    DispatchCorrelation,
    Dispatcher,
    EventSink,
)
from .stream_parser import SubagentStreamParser

_SUBAGENT_KIND = {
    "speciality-worker": "worker",
    "speciality-verifier": "verifier",
}


class SpecialistDispatcher:
    def __init__(self, inner: Dispatcher, arbitrator: Arbitrator):
        self._inner = inner
        self._arb = arbitrator

    async def run_specialist(
        self,
        *,
        session_id,
        team_id: str,
        plan_node_id: str | None,
        specialist_name: str,
        specialist_prompt: str,
        worker_focus: str,
        verify_criteria: str,
        logical_model: str,
        subagent_defs: list[AgentDefinition],
        timeout_seconds: float = 300.0,
    ) -> dict[str, Any]:
        parent = await self._arb.create_dispatch(
            session_id=session_id, team_id=team_id,
            plan_node_id=plan_node_id,
            agent_kind="specialist", agent_name=specialist_name,
            logical_model=logical_model,
        )
        parent_id = parent["dispatch_id"]

        parser = SubagentStreamParser()
        tool_use_to_dispatch: dict[str, str] = {}

        async def sink(event: dict) -> None:
            step = parser.ingest(event)
            for start in step.starts:
                kind = _SUBAGENT_KIND.get(start.subagent_name, "worker")
                child = await self._arb.create_dispatch(
                    session_id=session_id, team_id=team_id,
                    plan_node_id=plan_node_id,
                    parent_dispatch_id=parent_id,
                    agent_kind=kind,
                    agent_name=start.subagent_name,
                    logical_model=logical_model,
                )
                tool_use_to_dispatch[start.tool_use_id] = child["dispatch_id"]
            for end in step.ends:
                d_id = tool_use_to_dispatch.get(end.tool_use_id)
                if d_id is not None:
                    await self._arb.close_dispatch(d_id, status="completed")

        agent = AgentDefinition(
            name=specialist_name, prompt=specialist_prompt,
            logical_model=logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=session_id, team_id=team_id,
            agent_id=specialist_name,
            dispatch_id=parent_id,
        )

        task_prompt = (
            f"Worker focus:\n{worker_focus}\n\n"
            f"Verify criteria:\n{verify_criteria}\n\n"
            "Invoke the speciality-worker subagent first. Pass it the "
            "worker focus and any relevant context. Then invoke the "
            "speciality-verifier subagent with the worker's output "
            "and the verify criteria. Return a single JSON object:\n"
            '{"result": <worker output>, "attempts": [{"worker_tool_use_id": '
            '"<id>", "verifier_tool_use_id": "<id or null>", '
            '"verdict": "pass"|"fail"}]}'
        )

        result = await self._inner.dispatch(
            agent=agent,
            prompt=task_prompt,
            logical_model=logical_model,
            response_schema=None,
            correlation=correlation,
            event_sink=sink,
            timeout_seconds=timeout_seconds,
        )

        await self._arb.close_dispatch(parent_id, status="completed")

        attempts_dec = (result.response or {}).get("attempts", []) \
            if isinstance(result.response, dict) else []
        created_result = await self._arb.create_result(
            session_id=session_id, team_id=team_id,
            specialist_id=specialist_name, passed=True,
            summary={"result": (result.response or {}).get("result")},
            plan_node_id=plan_node_id,
        )
        for n, a in enumerate(attempts_dec, 1):
            w_tu = a.get("worker_tool_use_id")
            v_tu = a.get("verifier_tool_use_id")
            w_dispatch = tool_use_to_dispatch.get(w_tu)
            if w_dispatch is None:
                continue
            v_dispatch = tool_use_to_dispatch.get(v_tu) if v_tu else None
            await self._arb.create_attempt(
                result_id=created_result.result_id,
                session_id=session_id,
                attempt_kind="speciality",
                attempt_number=n,
                worker_dispatch_id=w_dispatch,
                verifier_dispatch_id=v_dispatch,
                verdict=a.get("verdict"),
            )

        return {"response": result.response, "dispatch_id": parent_id}
```

- [ ] **Step 4: Export from dispatcher package**

In `plugins/dev-team/services/conductor/dispatcher/__init__.py`, add:

```python
from .specialist import SpecialistDispatcher  # noqa: F401
```

(Extend the existing `__all__` list if one exists. If the file is minimal, just add the import.)

- [ ] **Step 5: Run test — expect PASS**

Run: `pytest testing/unit/tests/conductor/test_specialist_dispatcher.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-team/services/conductor/dispatcher/specialist.py \
        plugins/dev-team/services/conductor/dispatcher/__init__.py \
        testing/unit/tests/conductor/test_specialist_dispatcher.py
git commit -m "feat(dispatcher): SpecialistDispatcher with child dispatch + attempt tracking"
git push
```

---

## Task 6: Switch `generic_realizer.py` to the specialist path

**Files:**
- Modify: `plugins/dev-team/services/conductor/generic_realizer.py`
- Create: `testing/unit/tests/conductor/test_generic_realizer_specialist_path.py`

- [ ] **Step 1: Write failing integration test**

`testing/unit/tests/conductor/test_generic_realizer_specialist_path.py`:

```python
"""Realizer now routes each plan_node through SpecialistDispatcher, so a
parent specialist dispatch + child worker/verifier dispatches appear in the
arbitrator for every realized node."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import NodeKind
from services.conductor.dispatcher.mock import MockDispatcher
from services.conductor.generic_realizer import make_generic_realizer
from services.conductor.team_loader import (
    SpecialistDef, SpecialtyDef, TeamManifest,
)


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_realizer_creates_specialist_dispatch_and_children(
    arb, run_async, session_id, tmp_path,
):
    run_async(arb.open_session(session_id, initial_team_id="devteam"))
    rm = run_async(arb.create_roadmap("R"))
    node = run_async(arb.create_plan_node(
        rm.roadmap_id, "idx", NodeKind.PRIMITIVE,
        node_id="n-idx",
        specialist="platform-database",
        speciality="indexing",
    ))

    manifest = TeamManifest(name="devteam", team_root=tmp_path)
    manifest.specialists["platform-database"] = SpecialistDef(
        name="platform-database",
        specialties={
            "indexing": SpecialtyDef(
                name="indexing", description="Index review",
                worker_focus="Review indexes.",
                verify="Query plan uses them.",
            ),
        },
    )

    dispatcher = MockDispatcher()
    async def fake(agent, prompt, logical_model, response_schema,
                   correlation, event_sink, timeout_seconds=300.0):
        await event_sink({
            "type": "tool_use", "id": "tu-w", "name": "Task",
            "input": {"subagent_type": "speciality-worker",
                      "description": "work", "prompt": "p"},
        })
        await event_sink({
            "type": "tool_result", "tool_use_id": "tu-w",
            "content": [{"type": "text", "text": "{}"}],
        })
        from services.conductor.dispatcher.base import DispatchResult
        return DispatchResult(
            response={"result": {"ok": True},
                       "attempts": [{"worker_tool_use_id": "tu-w",
                                      "verdict": "pass"}]},
            duration_ms=1, events=2, terminated_normally=True,
        )
    dispatcher.dispatch = fake  # type: ignore[assignment]

    realize = make_generic_realizer(manifest)
    run_async(realize(arb, dispatcher, session_id, node.node_id))

    rows = run_async(arb._storage.fetch_all("dispatch"))
    kinds = sorted(r["agent_kind"] for r in rows)
    assert kinds == ["specialist", "worker"]

    attempts = run_async(arb._storage.fetch_all("attempt"))
    assert len(attempts) == 1
    assert attempts[0]["verdict"] == "pass"
```

- [ ] **Step 2: Run it — expect FAIL (realizer still on old path)**

Run: `pytest testing/unit/tests/conductor/test_generic_realizer_specialist_path.py -v`
Expected: FAIL — no "specialist" dispatch row.

- [ ] **Step 3: Rewrite `generic_realizer.py` to use SpecialistDispatcher**

Replace the body of `generic_realizer.py` (keep the module docstring + imports, replace the `realize` coroutine) with:

```python
"""Generic realizer — routes each plan_node's primitive through a specialist
subprocess. The specialist dispatches worker + verifier subagents internally
via the Task tool; the arbitrator records the parent specialist dispatch,
each child subagent dispatch, and the attempt grouping them.
"""
from __future__ import annotations

from uuid import UUID

from .arbitrator import Arbitrator
from .dispatcher import Dispatcher, SpecialistDispatcher
from .subagents import load_generic_subagents
from .team_loader import TeamManifest


def make_generic_realizer(
    manifest: TeamManifest,
    *,
    team_id: str | None = None,
):
    resolved_team_id = team_id or manifest.name
    subagent_defs = load_generic_subagents()

    async def realize(
        arbitrator: Arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
        node_id: str,
    ) -> None:
        node = await arbitrator.get_plan_node(node_id)
        if node is None:
            raise RuntimeError(f"plan_node {node_id} not found")
        if not node.specialist or not node.speciality:
            raise RuntimeError(
                f"generic realizer needs node.specialist + node.speciality; "
                f"got ({node.specialist!r}, {node.speciality!r}) on {node_id!r}"
            )
        specialty = manifest.get_specialty(node.specialist, node.speciality)
        if specialty is None:
            raise RuntimeError(
                f"specialty {node.specialist}.{node.speciality} not found "
                f"in team manifest {manifest.name!r}"
            )

        specialist_prompt = (
            f"You are the {node.specialist} specialist. Your job for this "
            f"plan_node is the {node.speciality} speciality.\n\n"
            "Use the speciality-worker subagent to do the work and the "
            "speciality-verifier subagent to check it. Return the final "
            "result plus an attempts array declaring the dispatch pairing "
            "and verdict."
        )

        sd = SpecialistDispatcher(inner=dispatcher, arbitrator=arbitrator)
        await sd.run_specialist(
            session_id=session_id,
            team_id=resolved_team_id,
            plan_node_id=node_id,
            specialist_name=node.specialist,
            specialist_prompt=specialist_prompt,
            worker_focus=specialty.worker_focus,
            verify_criteria=specialty.verify,
            logical_model=specialty.logical_model,
            subagent_defs=subagent_defs,
        )

    return realize
```

- [ ] **Step 4: Run new test — expect PASS**

Run: `pytest testing/unit/tests/conductor/test_generic_realizer_specialist_path.py -v`
Expected: 1 passed.

- [ ] **Step 5: Run the full conductor suite to catch regressions**

Run: `pytest testing/unit/tests/conductor/ --deselect testing/unit/tests/conductor/rollcall/test_rollcall.py::test_cli_rollcall_json_over_fixture_team --deselect testing/unit/tests/conductor/rollcall/test_rollcall.py::test_cli_rollcall_discovers_full_devteam -q`

Expected: the two CLI rollcall tests are pre-existing timeouts (deselected). Other pre-existing tests that exercise the old realizer path and expected a worker-agent dispatch may now fail — update each to expect `agent_kind='specialist'` or drive through a MockDispatcher that emits the new event shape. Fix as encountered.

**Known likely fixes (look for these patterns):**
- Any test asserting `result.specialist_id == "<x>-<y>-worker"` — the new path writes `specialist_id = node.specialist`, not `"<specialist>-<speciality>-worker"`. Update the assertion.
- Any test using `MockDispatcher` with the old response shape (`{"result": {...}}`) — extend the response to include `"attempts": []` so the specialist dispatcher doesn't try to create attempts against unknown tool_use_ids.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-team/services/conductor/generic_realizer.py \
        testing/unit/tests/conductor/test_generic_realizer_specialist_path.py \
        <any regression fix files>
git commit -m "feat(conductor): route primitives through SpecialistDispatcher"
git push
```

---

## Task 7: Mark this PR ready

- [ ] **Step 1: Verify all new tests pass**

```bash
pytest testing/unit/tests/conductor/contract/test_dispatch_schema.py \
       testing/unit/tests/conductor/contract/test_dispatch_api.py \
       testing/unit/tests/conductor/test_subagent_loader.py \
       testing/unit/tests/conductor/test_stream_parser.py \
       testing/unit/tests/conductor/test_specialist_dispatcher.py \
       testing/unit/tests/conductor/test_generic_realizer_specialist_path.py -v
```

Expected: all pass.

- [ ] **Step 2: Run full conductor + agenticteam suites for regression**

```bash
pytest testing/unit/tests/conductor/ testing/unit/tests/agenticteam/ \
   --deselect testing/unit/tests/conductor/rollcall/test_rollcall.py::test_cli_rollcall_json_over_fixture_team \
   --deselect testing/unit/tests/conductor/rollcall/test_rollcall.py::test_cli_rollcall_discovers_full_devteam -q
```

Expected: all non-deselected tests pass.

- [ ] **Step 3: Mark PR ready**

```bash
gh pr ready 32
```

---

## Self-Review

- **Scope:** Delivers the walking skeleton — specialist-as-parent with two generic subagents, parent+child dispatch tracking, attempt records. No real LLM integration, no parallel speciality dispatch, no in-specialist retry. All deferred items are flagged in Scope Notes.
- **Type consistency:** `AgentDefinition`, `DispatchCorrelation`, `DispatchResult` match `dispatcher/base.py`. `create_dispatch` / `close_dispatch` / `create_attempt` stay consistent across Task 2, Task 5, Task 6. `SubagentStart.subagent_name` is keyed to the file names `speciality-worker` / `speciality-verifier`.
- **No placeholders:** every step has complete code. Regression-fixing in Task 6 Step 5 is the only "fix as encountered" step, and it lists the two specific patterns to look for.
- **Commit cadence:** seven commits, one per task. Each pushable.
