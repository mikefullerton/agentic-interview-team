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

## Open items

- **Answer schemas.** `question.schema` is optional today. Decide whether to standardize on JSON Schema, a simpler enum-of-choices, or leave free-form until a real use case demands structure.
- **Cancellation semantics.** Can a host cancel an in-flight turn? If yes, add `cancel(session_id)` and a `state: "cancelled"` event; define how the conductor unwinds.
- **Multi-consumer fan-out.** One session, many observers (e.g. dashboard + chat window). Does `events()` fan out server-side, or is that the host's problem? Leaning server-side with a replay window keyed by `seq`.
- **Auth model for the WebSocket transport.** Out of scope for v1 beyond "bring your own reverse proxy", but the design should not preclude per-session tokens.
- **Relationship to `atp` CLI.** The `/atp run <team>` command today writes to stdout and blocks; in the new world, `atp` becomes one host (stdio transport) among several. Worth confirming before the plan is written.

## Followups

- Implementation plan — `docs/planning/2026-04-18-integration-surface-plan.md`. Ordered tasks:
  1. In-process reference transport + protocol test suite.
  2. Event projector from conductor `event`/`state`/`dispatch` → transport schema.
  3. Stdio adapter that wraps headless Claude Code.
  4. WebSocket transport (Python server).
  5. Swift `TeamClient` + a minimal chat-view harness that proves the contract end-to-end.
- Update `docs/planning/todo.md` to point "Plugin scheme for interacting with the team" at this doc.
- Revisit `docs/architecture.md` after the first two tasks land so the integration surface appears in the file map.
