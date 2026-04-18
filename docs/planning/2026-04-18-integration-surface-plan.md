# Integration Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Design doc:** [`2026-04-18-integration-surface-design.md`](./2026-04-18-integration-surface-design.md) — Session API, event schema, HITL targeting, transports, and the six-layer test structure live there. This plan is execution order; rationale lives in the design doc.

**Goal:** Ship the transport-neutral integration surface so any host (Mac chat app, CLI, Slack bot, web UI) can drive a dev-team without coupling to the conductor internals.

**Tech stack:** Python 3.13 (conductor side), pydantic for event/option schemas, `asyncio` generators for event streams, `starlette` + `uvicorn` for the WebSocket transport, Swift for the reference client.

---

## File Structure

### New (plugin runtime)

```
plugins/dev-team/services/integration_surface/
  __init__.py
  protocol.py                # Session API ABC, Event dataclasses, OptionSchema
  schemas/                   # JSON schemas per event kind (source of truth)
    event.text.json
    event.thinking.json
    event.tool_call.json
    event.question.json
    event.result.json
    event.error.json
    event.state.json
  in_process.py              # Reference transport — direct method calls
  stdio_ndjson.py            # Subprocess transport for headless Claude Code
  websocket_server.py        # Starlette app exposing the Session API
  projection/
    __init__.py
    event_projector.py       # conductor `event` → protocol `tool_call` / `state`
    state_projector.py       # node_state_event → protocol `state`
    request_projector.py     # `request` rows → `question`; answer → request
    dispatch_projector.py    # dispatcher attempts → `tool_call` lifecycle
  schema_lint.py             # Validator for emitted event streams
```

### New (tests)

```
testing/unit/tests/integration_surface/
  conftest.py                     # transport_factory parametrization
  contract/                       # 18 files — see design doc "Layout"
  transports/
  projection/
  hosts/
  integration/
  fixtures/
    fake_team.py
    recorded_sessions/
    schemas/                      # symlinks to services schemas
```

### New (hosts)

```
plugins/dev-team/hosts/
  cli/
    __init__.py
    main.py                  # reference CLI host; stdio transport
```

```
apps/mac-chat/               # Swift client + sample chat view (new top-level or linked submodule)
  TeamClient/                # package
  ChatSample/                # sample app target
```

### Modified

```
plugins/dev-team/skills/atp/scripts/atp_cli.py   # route commands through the Session API
docs/architecture.md                             # add integration surface to file map + diagrams
```

---

## Execution strategy

Tasks land in order — each task is green (tests pass) before the next one starts.

- **Tasks 1–4** are plugin-side Python. Each ships a vertical slice: new code + its test layer. Full model (judgment).
- **Task 5** (CLI host) is mechanical once protocol stabilizes. Fast model.
- **Task 6** (Swift client) is a separate repo/app; sequenced last so the Python protocol is frozen before Swift binds to it.

Every task ends with `pytest testing/unit/tests/integration_surface -q` green and a green `cc-verify`.

---

## Task 1 — In-process transport + protocol skeleton

**Files:**
- Create: `plugins/dev-team/services/integration_surface/protocol.py`
- Create: `plugins/dev-team/services/integration_surface/schemas/*.json`
- Create: `plugins/dev-team/services/integration_surface/in_process.py`
- Create: `plugins/dev-team/services/integration_surface/schema_lint.py`
- Create: `testing/unit/tests/integration_surface/fixtures/fake_team.py`
- Create: `testing/unit/tests/integration_surface/contract/**` (all 18 files)
- Create: `testing/unit/tests/integration_surface/conftest.py`

**Steps:**
- [ ] Define `TeamSession` ABC and typed `Event` dataclasses (`text`, `thinking`, `tool_call`, `question`, `result`, `error`, `state`) in `protocol.py`.
- [ ] Write JSON schemas for each event kind; snapshot them as frozen files.
- [ ] Implement `InProcessSession` against `TeamSession`. Uses an `asyncio.Queue` per session for outbound events; accepts a `TeamRunner` callable for turn execution.
- [ ] Implement `FakeTeam` in `fixtures/fake_team.py`: constructor takes a list of `(at_seq, event)` pairs plus reaction rules for `send` / `answer`.
- [ ] Implement `schema_lint.py` with the 5 violation kinds (unknown type, missing field, extra field, seq gap, duplicate seq).
- [ ] Write all 18 `contract/` test files. Tests take a `transport_factory` fixture; `conftest.py` currently parametrizes only `in_process`. Stdio and WebSocket are added in their tasks.
- [ ] Run the suite — green.
- [ ] Commit: `feat(integration-surface): in-process transport + protocol contract suite`.

**Done when:** `pytest testing/unit/tests/integration_surface/contract -q` green against the in-process transport; schema linter runs clean on every test.

---

## Task 2 — Projection layer

**Files:**
- Create: `plugins/dev-team/services/integration_surface/projection/*.py`
- Create: `testing/unit/tests/integration_surface/projection/*.py`
- Create: `testing/unit/tests/integration_surface/integration/test_in_process_smoke.py`
- Create: `testing/unit/tests/integration_surface/fixtures/recorded_sessions/in_process_puppy.ndjson`

**Steps:**
- [ ] `event_projector.py`: maps conductor `event` rows to `tool_call` (lifecycle: pending → running → succeeded/failed) and `state` events.
- [ ] `state_projector.py`: maps `node_state_event` rows (PLANNED / READY / RUNNING / DONE / FAILED / SUPERSEDED) to protocol `state` events.
- [ ] `request_projector.py`: maps human-addressed `request` kinds to `question`; a host `answer(...)` writes the matching response row.
- [ ] `dispatch_projector.py`: dispatcher attempt rows → `tool_call` status updates keyed by `attempt_id`.
- [ ] Write one test per projector asserting emitted protocol events; parameterize on the conductor resource under test.
- [ ] `test_in_process_smoke.py`: run the real conductor on `puppynamingteam` with the in-process transport; dump the event stream and diff against the golden recording.
- [ ] Commit: `feat(integration-surface): conductor → protocol projection layer`.

**Done when:** `pytest testing/unit/tests/integration_surface/projection testing/unit/tests/integration_surface/integration/test_in_process_smoke.py -q` green; golden recording checked in.

---

## Task 3 — Stdio NDJSON transport

**Files:**
- Create: `plugins/dev-team/services/integration_surface/stdio_ndjson.py`
- Create: `testing/unit/tests/integration_surface/transports/test_stdio_ndjson.py`
- Create: `testing/unit/tests/integration_surface/integration/test_stdio_smoke.py`
- Create: `testing/unit/tests/integration_surface/fixtures/recorded_sessions/stdio_puppy.ndjson`
- Modify: `testing/unit/tests/integration_surface/conftest.py` — add `stdio` to `transport_factory` params.

**Steps:**
- [ ] Implement `StdioSession` that spawns a subprocess, pipes NDJSON in/out, demultiplexes by `session_id`, and isolates stderr.
- [ ] Write `transports/test_stdio_ndjson.py` for transport-specific edges: line buffering, partial reads, subprocess death, SIGPIPE.
- [ ] Add `stdio` to `transport_factory`; confirm the full contract suite passes unchanged.
- [ ] `test_stdio_smoke.py`: real conductor over stdio; diff against the stdio-specific golden recording.
- [ ] Commit: `feat(integration-surface): stdio NDJSON transport`.

**Done when:** `pytest testing/unit/tests/integration_surface -q` green with `transport_factory ∈ {in_process, stdio}`.

---

## Task 4 — WebSocket transport

**Files:**
- Create: `plugins/dev-team/services/integration_surface/websocket_server.py`
- Create: `testing/unit/tests/integration_surface/transports/test_websocket.py`
- Create: `testing/unit/tests/integration_surface/integration/test_websocket_smoke.py`
- Create: `testing/unit/tests/integration_surface/fixtures/recorded_sessions/websocket_puppy.ndjson`
- Modify: `testing/unit/tests/integration_surface/conftest.py` — add `websocket` to `transport_factory` params.

**Steps:**
- [ ] Implement a Starlette app: `POST /sessions`, `POST /sessions/{id}/turns`, `POST /sessions/{id}/answers`, `DELETE /sessions/{id}`, `WS /sessions/{id}`.
- [ ] Implement `WebSocketSession` client that speaks the protocol against the server.
- [ ] Write `transports/test_websocket.py`: reconnect with `seq` replay, auth reject stub (placeholder — full auth is post-v1 per design doc), backpressure, unexpected close.
- [ ] Add `websocket` to `transport_factory`; full contract suite passes unchanged.
- [ ] `test_websocket_smoke.py`: real conductor behind the server; diff against the WebSocket golden recording.
- [ ] Commit: `feat(integration-surface): WebSocket transport`.

**Done when:** `pytest testing/unit/tests/integration_surface -q` green with all three transports; three-transport parity proven.

---

## Task 5 — Reference CLI host

**Files:**
- Create: `plugins/dev-team/hosts/cli/main.py`
- Create: `testing/unit/tests/integration_surface/hosts/test_cli_host.py`
- Modify: `plugins/dev-team/skills/atp/scripts/atp_cli.py` — route `/atp run <team>` through the CLI host.

**Steps:**
- [ ] CLI host: stdio transport + pretty-printing of `text` / `tool_call` / `question` / `result` events. HITL questions prompt interactively.
- [ ] Test exercises the host against `fake_team`: scripted events → captured stdout matches expected rendering.
- [ ] Rewire `atp_cli.py` to call the CLI host; existing `atp run` tests keep passing.
- [ ] Commit: `feat(integration-surface): reference CLI host`.

**Done when:** `pytest testing/unit/tests/integration_surface/hosts -q` green; `atp run puppynamingteam` behaves identically to today's output (smoke-verified by the existing atp test suite).

---

## Task 6 — Swift client + chat sample

**Files:**
- Create: `apps/mac-chat/TeamClient/` (Swift package — sources + tests)
- Create: `apps/mac-chat/ChatSample/` (minimal chat-view sample app)
- Create: `testing/unit/tests/integration_surface/hosts/test_swift_client_bridge.py`

**Steps:**
- [ ] Swift `TeamClient` package implements the Session API over WebSocket; publishes an `AsyncStream<Event>` for SwiftUI consumption.
- [ ] XCTests inside the Swift package cover the same contract surface (session lifecycle, HITL, resume) against a Python-side harness.
- [ ] Python-side bridge test (`test_swift_client_bridge.py`) spawns the Python WebSocket server + a scripted event sequence, invokes the Swift tests via `xcrun swift test`, asserts all pass.
- [ ] `ChatSample` renders `text` (streaming bubbles), `tool_call` (collapsible rows), `question[target=user]` (inline input). Other targets render as "waiting on …".
- [ ] Commit: `feat(integration-surface): Swift TeamClient + chat sample`.

**Done when:** Swift package tests green; bridge test green; `ChatSample` runs against a local Python server and a puppynaming team session completes end-to-end.

---

## Verification (cumulative)

After all six tasks:

1. **Three-transport parity.** Full `contract/` suite passes against in-process, stdio, WebSocket.
2. **Schema linter clean.** No kind-1..5 violations on any golden recording.
3. **HITL round-trip.** `question(target: "user")` → `answer(...)` → continuation, identical across transports.
4. **Resume fidelity.** `close` + `resume` picks up at stored `seq`.
5. **Projection round-trip.** Every conductor event/state/request/dispatch row type has a projection test.
6. **Host-side acceptance.** CLI host and Swift `TeamClient` both pass their host-side suites against `fake_team`.
7. **Integration smoke.** One real-conductor run per transport matches its golden recording.

---

## Architecture doc update

After Task 2 lands, open a follow-up PR that updates `docs/architecture.md` file map and diagrams to include the integration surface. Do not bundle with plan PRs — architecture changes deserve their own review.

---

## Open items deferred from the design doc

`Open items` in the design doc (answer schemas, cancellation, multi-consumer fan-out, auth model, relationship to `atp` CLI) are **not** in scope for this plan. Each lands as a follow-up once a real consumer needs it. The plan here ships a usable v1 without resolving them.
