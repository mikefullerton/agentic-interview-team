# 2026-04-18 — Integration Surface Design

> **Status:** Design summary. A concrete plan (`docs/planning/2026-04-18-integration-surface-plan.md`) will follow before implementation lands.
>
> **Purpose:** Define a transport-neutral plugin scheme for talking to a dev-team. Any host (native app, CLI, Slack bot, web UI) should be able to open a team session, stream events, answer HITL questions, and resume later — without knowing whether the team runs in-process, as a headless Claude Code subprocess, or on a remote server.
>
> **Relevant research:** [`docs/research/headless-claude-bidirectional.md`](../research/headless-claude-bidirectional.md) § "System architecture for production use".

## Goals

1. **One protocol, many transports.** The same contract works in-process (library), over stdio (NDJSON), and over the network (WebSocket / SSE).
2. **Bidirectional.** Hosts send user turns in; teams send text, tool activity, and HITL questions out.
3. **Resumable.** Sessions survive host restarts via `session_id` + `resume`.
4. **Host-neutral.** The Mac chat app, a shell, a Slack bot, and a future web UI all speak the same protocol — no host-specific branches in team code.

### Non-goals

- Defining how a team is authored. Teams remain markdown under `teams/<name>/`.
- Replacing the conductor's internal event stream. The integration surface is a *projection* of conductor events, not a parallel runtime.
- Specifying the Mac app's UI. Only the client-side protocol bindings.

## The plugin boundary

Two halves. A host calls **Session API** methods; the team emits **events** back.

### Session API (host → team)

| Call | Result | Purpose |
|---|---|---|
| `start(team, prompt?, options?)` | `SessionHandle { session_id }` | Open a new team session. `options` carries tool policy (`allowed_tools`, `max_turns`, `permission_mode`). |
| `send(session_id, user_turn)` | `()` | Append a user turn to an open session. |
| `events(session_id)` | `AsyncIterator<Event>` | Subscribe to the event stream. Single logical stream per session. |
| `answer(session_id, question_id, content)` | `()` | Respond to a `question` event. `content` is free-form text or a structured payload. |
| `resume(session_id)` | `SessionHandle` | Re-attach to a parked session by id. |
| `close(session_id, reason?)` | `()` | End the session (graceful or aborted). |

`start` and `resume` are the only calls that create a handle. Everything else takes a `session_id`. This keeps the contract restartable — a host that crashes can resume purely from the stored id.

### Event schema (team → host)

Every event is tagged with `session_id` and a monotonic `seq` so hosts can dedupe on resume.

| Event | Payload | Notes |
|---|---|---|
| `text` | `{ role, delta \| text }` | Streaming assistant text. `delta` for tokens, `text` for whole blocks. |
| `thinking` | `{ text }` | Optional; hosts may choose not to render. |
| `tool_call` | `{ tool_use_id, name, input, status }` | `status`: `running` / `succeeded` / `failed`. One tool call yields 2–3 events over its lifetime. |
| `question` | `{ question_id, target, prompt, schema? }` | HITL ask. `target` is a logical role (`user`, `product_owner`, `sre_oncall`, …). `schema` optionally constrains the answer. |
| `result` | `{ stop_reason, usage, cost_usd, num_turns }` | Turn complete. |
| `error` | `{ kind, message, retryable }` | Transport or model error. |
| `state` | `{ phase, detail? }` | Lifecycle: `starting` / `awaiting_input` / `parked` / `closed`. |

The schema deliberately tracks stream-json shapes from headless Claude Code so the stdio adapter is thin (see "Transports" below). Team-internal concepts (conductor gates, dispatcher attempts, roadmap node state) are **not** surfaced directly — they map to `state` or `tool_call` events at the boundary.

### HITL targeting

`question.target` is a logical role, not an address. The host decides how to route:

- A chat app routes every question to the current user.
- A Slack bot posts `target: "product_owner"` to `#product` and `target: "sre_oncall"` to the on-call pager.
- A batch runner parks the session when any question arrives and pings the owner out-of-band.

Teams never encode host policy. They say *who should answer*; the host decides *how to reach them*.

## Transports

Three reference transports share the same protocol. A host picks one at connection time; teams are unaware of which is in use.

### 1. In-process (library)

Python host imports the team runtime directly. `Session API` calls are method calls; events are yielded from an async generator. Zero serialization. The reference transport — all protocol tests run against it.

### 2. Stdio subprocess (NDJSON)

Host spawns `claude -p --input-format stream-json --output-format stream-json --verbose` (or an equivalent team runner) and speaks line-delimited JSON over stdin/stdout. Each protocol message serializes to one line. Maps near-directly onto the events documented in `headless-claude-bidirectional.md`. Session id comes from the `system/init` event.

This is the path a plugin for another editor / tool that already has a subprocess story would take.

### 3. WebSocket / SSE

A Python server hosts the team runtime and exposes:

- `POST /sessions` → `{ session_id }` (wraps `start`)
- `POST /sessions/{id}/turns` (wraps `send`)
- `POST /sessions/{id}/answers` (wraps `answer`)
- `DELETE /sessions/{id}` (wraps `close`)
- `GET /sessions/{id}/events` → SSE **or** `WS /sessions/{id}` for full duplex

Auth, TLS, and reconnect are the transport's problem, not the protocol's. This is the path the Mac chat app takes.

## Walkthrough: native Mac chat app

Goal: ship a Mac app whose chat window is a host for any dev-team, with no Python in the app bundle.

```
┌─ Mac app (Swift) ────────────┐        ┌─ Team runtime (Python) ──────┐
│                              │        │                              │
│  ChatView                    │        │  Conductor.run_roadmap       │
│    ↕                         │  WS    │    ↕                         │
│  TeamClient (Swift)          │◀──────▶│  WebSocket server            │
│    - open(url, team)         │  JSON  │    - Session API handlers    │
│    - send(turn)              │        │    - Event fan-out           │
│    - answer(qid, text)       │        │                              │
│    - events stream           │        │                              │
└──────────────────────────────┘        └──────────────────────────────┘
```

1. User types in ChatView → `TeamClient.send`.
2. `text` events stream in; the view appends tokens to the bubble.
3. `tool_call` events render as collapsible activity rows (`name`, `input`, final `status`).
4. A `question` event with `target: "user"` opens an inline prompt in the chat. User's reply → `TeamClient.answer`.
5. A `question` event with `target: "product_owner"` (and that role isn't the current user) renders as a "waiting on Alice" card; the app may route out-of-band.
6. `result` finalizes the turn. `state: "parked"` collapses the session; `resume(session_id)` on next app launch rehydrates it.

No Claude Code specifics leak into the Swift code. Swapping the team runtime for a different backend is a URL change.

## Mapping to existing code

The integration surface sits **above** the conductor and **beside** the arbitrator. Nothing in the schema or conductor loop changes.

- **Event stream** is produced by projecting conductor `event` + `state` + `dispatch` rows into the transport-neutral schema. The projection layer is the only new translation — teams keep writing the existing events.
- **Questions** already exist as `request` rows with typed kinds. A subset of request kinds (the ones that need a human) become `question` events at the boundary; the host's `answer(...)` call writes the response back into `request`-matched storage.
- **Sessions** — `session_id` here is the same `session_id` the arbitrator already tracks. `resume(session_id)` maps to the existing session-resume path that `run_roadmap` uses.
- **Policy** — tool allowlist / max turns / permission mode flow through to whichever runtime is handling the turn (conductor's own tool dispatch, or a spawned headless Claude process for a specialist invocation).

## Testing

The whole point of a transport-neutral protocol is that hosts can swap transports without reasoning about the team runtime. Tests prove that promise. Six layers, mirroring the arbitrator contract-test pattern established in PR #23.

### Layout

```
testing/unit/tests/integration_surface/
├── contract/                    # protocol conformance — runs against every transport
│   ├── conftest.py               # transport_factory fixture (parametrized)
│   ├── test_session_lifecycle.py      # start / send / events / close / resume
│   ├── test_state_machine.py          # legal/illegal phase transitions
│   ├── test_event_ordering.py         # seq monotonic, no gaps, no duplicates
│   ├── test_event_schema_conforms.py  # schema linter over emitted events
│   ├── test_hitl_roundtrip.py         # question → answer → continuation
│   ├── test_hitl_targeting.py         # target field preserved verbatim
│   ├── test_hitl_unanswered.py        # parked session with pending question
│   ├── test_policy_flowthrough.py     # allowed_tools, disallowed_tools honored
│   ├── test_policy_max_turns.py       # terminal result at limit
│   ├── test_policy_permission_mode.py # default vs bypass observable in events
│   ├── test_error_kinds.py            # each error kind surfaces, retryable flag correct
│   ├── test_cancellation.py           # (gated on "cancel" open item)
│   ├── test_multi_session_isolation.py # session A events don't leak into B
│   ├── test_fanout.py                 # multiple subscribers, seq-aligned replay
│   ├── test_resume_fidelity.py        # events resume at stored seq, no drift
│   ├── test_large_payloads.py         # large tool_call.input, long text blocks
│   └── test_determinism.py            # scripted team → identical event sequences
├── transports/                   # transport-specific internals
│   ├── test_in_process.py             # backpressure, generator close semantics
│   ├── test_stdio_ndjson.py           # line buffering, partial reads, stderr isolation
│   └── test_websocket.py              # reconnect with last-seq, auth reject, tls
├── projection/                   # conductor → protocol event mapping
│   ├── test_event_projection.py       # conductor `event` rows → `tool_call` / `state`
│   ├── test_state_projection.py       # node_state_event → protocol `state` event
│   ├── test_request_projection.py     # `request` rows → `question` events, answer round-trip
│   ├── test_dispatch_projection.py    # dispatcher attempts → `tool_call` lifecycle
│   └── test_policy_projection.py      # options.allowed_tools → conductor tool gate
├── hosts/                        # host/adapter tests driven by fake_team
│   ├── test_cli_host.py               # reference CLI host → text output, prompts
│   ├── test_swift_client_bridge.py    # pyobjc/xcrun harness against Swift TeamClient
│   └── test_slack_host_sketch.py      # smoke for target-based routing
├── integration/                  # real conductor, one per transport
│   ├── test_in_process_smoke.py
│   ├── test_stdio_smoke.py
│   └── test_websocket_smoke.py
└── fixtures/
    ├── fake_team.py                   # scripts event sequences without booting conductor
    ├── recorded_sessions/             # captured event streams used as golden files
    └── schemas/                       # typed JSON schemas per event kind
```

### Six test layers

1. **Protocol contract tests** (`contract/`). One suite, parametrized on a `transport_factory` fixture that yields a live session for each of the three transports. Every test runs three times. A new transport is proven correct by passing this suite — no bespoke tests per transport for protocol behavior. Covers: session lifecycle, state-machine transitions, event ordering (`seq` monotonic with no gaps, no duplicates), event schema conformance, HITL round-trip and targeting, parked-with-pending-question, policy flow-through (allowed/disallowed tools, max turns, permission mode), every `error.kind` and its `retryable` flag, cancellation (if adopted), multi-session isolation, multi-consumer fan-out with replay, resume fidelity, large-payload handling, and determinism (scripted team → identical event sequences across runs and transports).

2. **Event schema conformance** (`test_event_schema_conforms.py`). Analogue of `plugins/dev-team/scripts/db/schema_lint.py`. JSON schemas under `fixtures/schemas/` define the allowed shape of each event kind. The linter fails on (a) unknown `type`, (b) missing required field, (c) extra field, (d) `seq` gap, (e) duplicate `seq`. Every recorded session in `fixtures/recorded_sessions/` is re-validated on each test run; any transport that smuggles a non-conformant payload fails immediately.

3. **Transport internals** (`transports/`). Per-transport edge cases that don't belong in the protocol suite. Stdio: line-buffered readline vs partial reads, stderr isolation so child diagnostics don't pollute stdout NDJSON, subprocess death mid-stream, `SIGPIPE` on closed stdin. WebSocket: reconnect with last-seq replay, auth reject on missing/invalid token, TLS termination, unexpected close frame, backpressure when the slow consumer lags. In-process: async-generator `close()` semantics, task cancellation during iteration, event drop if subscriber awaits too slowly.

4. **Projection layer** (`projection/`). Verifies the translation from conductor primitives to the protocol schema. For each conductor source (`event`, `node_state_event`, `request`, `dispatch`, `attempt`) there's a test that seeds rows, runs the projector, and asserts the emitted protocol events. Includes the inverse: a host `answer(...)` writes the expected row back into `request`-matched storage. Catches drift the moment a new conductor event kind appears without a projection rule.

5. **Host-side tests** (`hosts/`). Reference hosts built against `fake_team` so they can be tested end-to-end without a live conductor. A minimal CLI host (stdio transport) is in-tree and functions as both demo and test subject. The Swift `TeamClient` is exercised via a bridge harness (pyobjc or an `xcrun`-driven swift test) that scripts events from the Python side and asserts the Swift-side callbacks. A Slack host exists only as a smoke test to prove target-based routing works when "current user" isn't the answerer.

6. **Integration smoke** (`integration/`). One end-to-end test per transport against the real conductor. Exercises a canonical team (a three-node roadmap from `teams/puppynamingteam/`), collects the emitted event stream, and diffs it against a golden file in `fixtures/recorded_sessions/`. Purpose: catch projection-layer breakage that contract tests (running against `fake_team`) can't see. Gated by the same `AGENTIC_REAL_LLM_SMOKE=1` pattern used by existing functional tests when the team requires real model calls.

### Fake team runtime

`fixtures/fake_team.py` scripts event sequences without booting the conductor. Constructor takes a list of `(at_seq, event)` pairs plus rules for how to react to `send` / `answer` calls. Host-side tests and the bulk of the contract suite run against the fake so they exercise realistic event shapes without a live team. The fake is the single source of truth for "what the protocol allows" — every shape appearing in the schemas is produced by at least one fake sequence.

### Recorded sessions as golden files

`fixtures/recorded_sessions/` holds captured event streams (NDJSON) from canonical runs: a plain text turn, a tool-call turn, a HITL turn, a parked-and-resumed session, a failed turn, a cancelled turn. Golden-file diff tests in each test layer reference these recordings, so contract regressions show up as a readable unified diff instead of buried asserts.

### Verification items

Borrowing the pattern from the atp roadmap contract tests:

1. **Schema linter runs clean against every transport.** No kind-1 (unknown `type`), kind-2 (missing required field), kind-3 (extra field), kind-4 (`seq` gap), or kind-5 (duplicate `seq`) violations during any canonical session.
2. **Three-transport parity.** The full `contract/` suite passes against all three `transport_factory` values.
3. **HITL round-trip across transports.** `question(target: "user")` → host `answer(...)` → team continuation with the answer visible in the next `text` event, identically over in-process, stdio, and WebSocket.
4. **Resume fidelity.** After `close` + `resume`, events picked up at the stored `seq` match the original stream (modulo replay window policy decided in "Open items").
5. **Projection round-trip.** Every conductor event/state/request/dispatch row type has a corresponding projection test that asserts the emitted protocol event; inverse mapping for `answer → request` verified.
6. **Host-side acceptance.** Reference CLI host and Swift `TeamClient` both pass their host-side suites driven by `fake_team`.
7. **Integration smoke.** One end-to-end run per transport against `puppynamingteam` matches its golden recording.

## Open items

- **Answer schemas.** `question.schema` is optional today. Decide whether to standardize on JSON Schema, a simpler enum-of-choices, or leave free-form until a real use case demands structure.
- **Cancellation semantics.** Can a host cancel an in-flight turn? If yes, add `cancel(session_id)` and a `state: "cancelled"` event; define how the conductor unwinds.
- **Multi-consumer fan-out.** One session, many observers (e.g. dashboard + chat window). Does `events()` fan out server-side, or is that the host's problem? Leaning server-side with a replay window keyed by `seq`.
- **Auth model for the WebSocket transport.** Out of scope for v1 beyond "bring your own reverse proxy", but the design should not preclude per-session tokens.
- **Relationship to `atp` CLI.** The `/atp run <team>` command today writes to stdout and blocks; in the new world, `atp` becomes one host (stdio transport) among several. Worth confirming before the plan is written.

## Followups

- Implementation plan — `docs/planning/2026-04-18-integration-surface-plan.md`. Ordered tasks (each lands with its corresponding slice of the test layout above):
  1. In-process reference transport + `fake_team` + full `contract/` suite + event schemas.
  2. Projection layer from conductor `event`/`state_event`/`request`/`dispatch` → transport schema + `projection/` tests.
  3. Stdio adapter that wraps headless Claude Code + `transports/test_stdio_ndjson.py` + `integration/test_stdio_smoke.py`.
  4. WebSocket transport (Python server) + `transports/test_websocket.py` + `integration/test_websocket_smoke.py`.
  5. Reference CLI host + `hosts/test_cli_host.py`.
  6. Swift `TeamClient` + bridge harness + chat-view sample app.
- Update `docs/planning/todo.md` to point "Plugin scheme for interacting with the team" at this doc.
- Revisit `docs/architecture.md` after the first two tasks land so the integration surface appears in the file map.
