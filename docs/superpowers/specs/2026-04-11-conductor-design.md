# 2026-04-11 — Conductor Architecture Design Spec

> **Status:** Design spec. Prescriptive. Ready to inform an implementation plan.
>
> **Research predecessor:** [`docs/planning/2026-04-11-conductor-architecture.md`](../../planning/2026-04-11-conductor-architecture.md) — captures the brainstorming session, alternatives considered, and decision history. This spec is the crisper, prescriptive distillation.
>
> **Terminology ancestor:** [`docs/planning/2026-04-03-system-architecture-v2.md`](../../planning/2026-04-03-system-architecture-v2.md) — original DB-centric rearchitecture. Superseded by the research predecessor but its terminology and disposition tables stand.

---

## 1. Purpose & Scope

Define the target architecture for the agentic dev-team system: a headless **conductor** process that runs agentic pipelines outside any Claude Code conversation, dispatching LLM work through a pluggable **dispatcher** layer, with all state and communication flowing through a single **arbitrator** over a shared DB.

**In scope:**
- Component responsibilities and contracts.
- Data model (resources, keys, relationships).
- Runtime behavior (session lifecycle, main loop, dispatch lifecycle, state tree).
- Inter-team coordination protocol.
- Team-lead authoring model (Python team-playbooks).
- Host integration (terminal, agentic-daemon).
- Error handling, crash recovery, migration, testing strategy.

**Out of scope:**
- Specific team-playbook content for any given team.
- Backend choice for arbitrator storage beyond "SQLite and markdown are supported."
- UI implementation details beyond the client contract.
- LocalDispatcher implementation (deferred until a concrete open-source target is chosen).
- Roadmaps-v2 (sessions as steps in larger plans) — a separate layer above the conductor.

---

## 2. Goals & Non-Goals

### Goals

1. **Conversation-free outer loop.** Zero context accumulation in any Claude Code conversation for the main pipeline. Long runs are cheap.
2. **Parallel specialist dispatch.** Independent specialists run concurrently without cross-contamination.
3. **Shared data plane.** Inter-team coordination is a query, not a message bus.
4. **LLM portability.** The LLM vendor is a dispatcher seam, not a system assumption. Mixing concrete models across agents is a config decision.
5. **Crash recovery without rework.** Persisted state tree lets a conductor restart from the last completed node; completed findings are not recomputed.
6. **Deterministic orchestration.** Retry logic, routing, gating, and state transitions are pure Python. LLMs are only called at explicit judgment points with schema-validated responses.
7. **Live observability.** The user can watch any dispatch in real time through a dispatcher-forwarded stream, at zero cost to the conductor's own context.
8. **Subscription compatibility.** The default dispatcher works with a Claude Max subscription (no per-token API billing).

### Non-goals

- Replacing Claude Code as a user-facing coding tool.
- Hosting arbitrary long-lived Claude Code conversations.
- Providing a drop-in replacement for the current workflow markdown prose files (those are migrated team-by-team when their turn comes).
- Per-token API billing as the default cost model.
- Cross-session orchestration (that's roadmaps-v2 territory).

---

## 3. Terminology

| Term | Meaning |
|---|---|
| **Conductor** | Long-running Python process, one per session. Schedules, dispatches, forwards events. Not an LLM. |
| **Arbitrator** | Single API facade over the shared DB. Python library, optionally exposed over HTTP. The only contract anyone talks through. |
| **Dispatcher** | LLM vendor abstraction. `ClaudeCodeDispatcher` (default), future `LocalDispatcher`, etc. |
| **Team-lead** | State machine scaffold with LLM-driven judgment nodes. One per active team. |
| **Team-playbook** | Static authored definition of a team: state machine, judgment specs, manifest. Python module. |
| **Session** | The data scope for a pipeline run. All rows keyed by `session_id`. Runtime instance of one or more team-playbooks. |
| **State tree** | Ephemeral, tree-shaped cursor of active work. Push on dispatch, pop on completion. Persisted to DB for crash recovery. |
| **Specialist** | Stateless dispatched task. Owns one or more specialties. Returns structured result to team-lead. |
| **Specialty** | Worker/verifier pair focused on one cookbook artifact. (Renamed from `specialty-team`.) |
| **Specialty-worker** | LLM call producing structured findings. |
| **Specialty-verifier** | LLM call checking a worker's findings for completeness. |
| **Consultant** | Cross-cutting reviewer. Worker/verifier pair applied across specialty outputs. |
| **Persona** | LLM call translating raw findings into persona-voiced interpretations. No new findings. |
| **Observer** | Dispatcher-forwarded event stream. Each dispatch emits events to the arbitrator `event` resource. |
| **Request** | Explicit inter-team request/response. Typed by `kind` with input/response schemas, mandatory timeouts, arbitrator-internal serial queue. |
| **Logical model name** | Per-agent cost tier (`high-reasoning`, `fast-cheap`, `balanced`, `local`). Mapped to concrete models by the dispatcher. |

---

## 4. Architecture Overview

### 4.1 Topology

```
┌──────────────┐    ┌────────────────────────────────────────┐
│  User        │    │         Conductor (Python)             │
│  Interface   │    │                                        │
│  (TUI/web/   │◄──►│  ┌────────┐   ┌──────────┐             │
│   repl/cc/   │    │  │ Main   │──►│ Team-lead│             │
│   none)      │    │  │ loop   │◄──│   FSM    │             │
└──────┬───────┘    │  └────┬───┘   └──────────┘             │
       │            │       │                                │
       │            │       ▼                                │
       │            │  ┌─────────┐    ┌────────────────┐     │
       │            │  │Dispatch │───►│  Dispatcher    │     │
       │            │  │ layer   │    │ (ClaudeCode)   │     │
       │            │  └────┬────┘    └────┬───────────┘     │
       │            │       │              │                 │
       │            │       │              ▼                 │
       │            │       │        ┌──────────────┐        │
       │            │       │        │ claude -p    │        │
       │            │       │        │ subprocess   │        │
       │            │       │        └──────────────┘        │
       │            └───────┼──────────────────────────────┬─┘
       │                    │                              │
       ▼                    ▼                              ▼
┌────────────────────────────────────────────────────────────┐
│                   Arbitrator (single instance)             │
│  Python library / optional HTTP wrapper                    │
│  Resources: session, state, message, gate, result,         │
│  finding, interpretation, event, task, request,            │
│  project-item, schedule, todo, issue, concern,             │
│  dependency, decision                                      │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │ Storage backend│
                 │ sqlite|markdown│
                 └────────────────┘
```

### 4.2 Hard rules

- **One arbitrator per session.** All components read and write through it.
- **One conductor per session.** No multi-session conductors.
- **Dispatcher is the only code that touches a concrete LLM.** Everything above it speaks "run agent X with prompt Y, expect response Z."
- **Team-leads don't hold state in memory long-term.** State lives as an ephemeral reference during a step, and is persisted to the DB on every push/pop.
- **Workers are isolated.** A worker never sees verifier instructions; a consultant never sees worker prompts.
- **User-facing speech is the team-lead's job only.** Specialists and workers don't talk to the user.
- **Every inter-component write is schema-validated.** Messages, results, findings, request inputs/responses — all constrained.

### 4.3 Guiding principle

**Intelligence at the edges, deterministic plumbing in the middle.** User interfaces and LLM workers are the only places LLM thinking happens. Everything between them is Python and SQL.

---

## 5. Component Specifications

### 5.1 Conductor

**Responsibility:** Run the session's main loop. Dispatch work. Forward events. Persist state.

**Lifecycle:**
- Started with `conductor start --session-id <uuid> --playbook <path> [--ui tui|web|repl|cc|none] [--dispatcher claude-code|local|...] [--storage sqlite|markdown] [--host terminal|daemon]`.
- Loads the team-playbook module.
- Opens (or creates) the session in the arbitrator.
- Runs the main loop until the session is complete or interrupted.
- On interrupt: writes the current state to the DB and exits cleanly. Next start with the same `--session-id` resumes from the persisted state tree.

**Main loop (per tick):**
1. Pull next pending task from the arbitrator for this session.
2. Ask the team-lead state machine: "given the current state node, what's next?" — returns `{ actions, next_state }`.
3. Execute actions (dispatch specialists, write gates, emit messages, update state) as async tasks.
4. Forward dispatcher events to the arbitrator as they arrive.
5. On dispatch completion, write `result` / `finding` / `interpretation` rows and push/pop the state tree.
6. Handle user input tasks (messages, verdicts) inline.
7. Checkpoint — all of the above is durable through the arbitrator.
8. Idle until new work arrives or the session completes.

**Not the conductor's job:**
- Choosing what to say to the user (team-lead does that).
- Deciding whether to retry (team-lead state machine does that).
- Knowing anything about the backend (arbitrator handles that).
- Knowing anything about the concrete LLM (dispatcher handles that).

**Invariants:**
- Every action the conductor takes is either a pure DB write or a dispatcher call.
- The main loop is single-threaded async; parallelism comes from awaiting multiple dispatcher calls concurrently.
- A conductor with no work in its queue must idle cheaply (no polling tight-loop).

### 5.2 Arbitrator

**Responsibility:** The single point of contact for all data and all coordination.

**API shape** (Python, all async):

```python
class Arbitrator:
    # Lifecycle
    async def open_session(self, session_id: UUID, team_id: str, metadata: dict) -> Session: ...
    async def close_session(self, session_id: UUID, status: SessionStatus) -> None: ...

    # Generic resource CRUD (one method family per resource)
    async def create_<resource>(self, session_id, team_id, ...) -> <Resource>: ...
    async def get_<resource>(self, session_id, team_id, id) -> <Resource>: ...
    async def list_<resources>(self, session_id, team_id, filter=...) -> list[<Resource>]: ...
    async def update_<resource>(self, ...) -> <Resource>: ...

    # Event stream
    async def emit_event(self, session_id, team_id, kind, payload) -> None: ...
    async def subscribe_events(self, session_id, filter=...) -> AsyncIterator[Event]: ...

    # Inter-team requests
    async def request(self, session_id, from_team, to_team, kind, input) -> RequestHandle: ...
    async def await_response(self, handle) -> RequestResponse: ...
    async def register_request_handler(self, team_id, kind, handler) -> None: ...

    # Task queue
    async def enqueue_task(self, session_id, team_id, kind, payload) -> Task: ...
    async def next_task(self, session_id) -> Task | None: ...
    async def complete_task(self, task_id, result) -> None: ...
```

**Backend abstraction:** `--storage sqlite|markdown|...` selects the concrete backend. The arbitrator is the only component that knows the backend exists. Backends implement a narrow `Storage` protocol (read row, write row, stream rows, transaction).

**HTTP wrapper (optional):** A thin Flask/FastAPI app that exposes the same API over HTTP for out-of-process clients (web UI, daemon-hosted attach clients). The Python library and HTTP wrapper are functionally identical from the caller's perspective.

**Invariants:**
- Every resource row carries `(session_id, team_id)` as part of its primary key or unique constraint (except `request`, which has `from_team` and `to_team`).
- Schema validation happens at write time. No silent acceptance of malformed data.
- Writes are durable before they return.
- The arbitrator is the serial funnel for inter-team requests (see §7).

### 5.3 Dispatcher

**Responsibility:** Abstract LLM vendor. Accept a structured dispatch request, return a structured response, stream events.

**Interface:**

```python
class Dispatcher(Protocol):
    async def dispatch(
        self,
        agent: AgentDefinition,
        prompt: str,
        logical_model: str,  # "high-reasoning" | "fast-cheap" | ...
        response_schema: dict | None,
        session_id: UUID,
        correlation: DispatchCorrelation,  # session_id, team_id, agent_id
        event_sink: EventSink,
    ) -> DispatchResult: ...
```

**`DispatchResult`:**
```
{
  "response": <validated structured response or text>,
  "duration_ms": <int>,
  "events": <count of emitted events>,
  "terminated_normally": <bool>,
  "error": <optional error details>,
}
```

**Concrete implementations:**

#### 5.3.1 `ClaudeCodeDispatcher` (default)

- Spawns `claude -p` as an async subprocess via `asyncio.create_subprocess_exec`.
- Passes:
  - `--agents '<json>'` — inline agent definitions built from the project's `agents/` markdown files at conductor startup.
  - `--output-format stream-json` — newline-delimited JSON event stream.
  - `--include-partial-messages` — token-level events.
  - `--include-hook-events` — hook lifecycle events.
  - `--session-id <uuid>` — forced session ID for correlation.
  - `--json-schema <schema>` — when `response_schema` is provided; enforces structured output at the CLI boundary.
  - `--model <concrete-id>` — resolved from `logical_model`.
  - `--bare` — no auto-discovery of settings; the agent carries its own context.
- Reads subprocess stdout line-by-line, parses each line as JSON, forwards to `event_sink`.
- Parses the final result event, validates against `response_schema`, returns `DispatchResult`.
- Uses the user's Claude subscription (Max/Pro). No per-token API billing.

#### 5.3.2 `LocalDispatcher` (deferred)

- Wraps a locally-hosted open-source model.
- Same interface, same event shape.
- Exact runner (Ollama, vLLM, llama.cpp, etc.) and target model are a remaining open question.

#### 5.3.3 Logical-to-concrete model mapping

Configured per dispatcher instance:

```python
ClaudeCodeDispatcher(model_map={
    "high-reasoning": "claude-opus-4-6",
    "balanced": "claude-sonnet-4-6",
    "fast-cheap": "claude-haiku-4-5-20251001",
})
```

`LocalDispatcher` would map the same logical names to local model identifiers.

**Invariants:**
- A dispatcher never touches the arbitrator directly — it emits events through the provided `event_sink`.
- A dispatcher call either returns a structurally valid response or raises a typed error.
- `claude -p` subprocess lifecycle is fully managed: stdin closed immediately, stdout drained fully, process reaped, wall-clock timeout enforced.

### 5.4 Team-Lead (State Machine + Judgment)

**Responsibility:** Given a session state, decide the next action.

**Shape:** A team-lead is an instantiation of a team-playbook's state machine. It is *driven* by the conductor — the conductor asks it "what's next?" and it returns `{ actions, next_state }`.

**Structure:**
- **States** — named nodes. Each has entry actions, exit actions, and a set of legal successors.
- **Transitions** — legal `(state, event) → next_state` pairs.
- **Judgment specs** — named (prompt-template + response-schema + legal-successors) tuples that specific states invoke when their decision requires an LLM judgment.
- **Manifest** — specialists and specialties the team uses.
- **Retry policy** — per-action retry counts and escalation rules.

**Judgment call flow:**
1. State machine reaches a judgment node.
2. Team-lead builds a prompt from the judgment spec's template and current state.
3. Team-lead asks the conductor to dispatch the judgment through the dispatcher.
4. Dispatcher returns a schema-validated response, typically `{ next_action, reasoning, next_state }`.
5. Team-lead validates `next_state` is a legal successor of the current state.
6. On success: transition. On schema or legality failure: retry once, then escalate (gate the user).

**Invariants:**
- No free-form LLM loops. Every LLM call happens at a declared judgment node with a declared schema.
- No hidden transitions. Every successor state is in the declared transition table.
- All state changes go through the conductor's state-tree update path, not direct DB writes.

### 5.5 Team-Playbook (Authoring Format)

**Format:** Python module. One file per playbook.

**Convention:** **Declarations, not programs.** The author expresses the team's shape as data — dicts, dataclasses, lists — not as control flow.

**Minimum contents:**

```python
# playbooks/name_a_puppy.py
from conductor.playbook import State, Transition, JudgmentSpec, Manifest, TeamPlaybook

STATES = [
    State("start", entry_actions=[...]),
    State("gather_traits", judgment="ask_next_question"),
    State("dispatch_specialists", entry_actions=[
        DispatchSpecialist("breed"),
        DispatchSpecialist("lifestyle"),
        DispatchSpecialist("temperament"),
    ]),
    State("aggregate", entry_actions=[AggregateFindings()]),
    State("present", entry_actions=[PresentFinalNames()]),
    State("done"),
]

TRANSITIONS = [
    Transition("start", "gather_traits"),
    Transition("gather_traits", "gather_traits"),  # loop
    Transition("gather_traits", "dispatch_specialists"),
    Transition("dispatch_specialists", "aggregate"),
    Transition("aggregate", "present"),
    Transition("present", "done"),
]

JUDGMENT_SPECS = {
    "ask_next_question": JudgmentSpec(
        prompt_template="...",
        response_schema={...},
        legal_next_states=["gather_traits", "dispatch_specialists"],
        logical_model="balanced",
    ),
}

MANIFEST = Manifest(
    specialists=["breed", "lifestyle", "temperament"],
)

PLAYBOOK = TeamPlaybook(
    name="name-a-puppy",
    states=STATES,
    transitions=TRANSITIONS,
    judgment_specs=JUDGMENT_SPECS,
    manifest=MANIFEST,
    initial_state="start",
)
```

**Rules:**
- No module-level side effects besides constructing the `PLAYBOOK` object.
- No imperative control flow inside state declarations — entry actions are action objects, not arbitrary callables with business logic.
- Custom action classes may be defined in the same file if local; shared actions live in `conductor.actions`.

**Lint check (future):** Enforce declaration discipline mechanically. See §18.

### 5.6 Specialist

**Responsibility:** Run one or more specialties against a target, aggregate results, return a structured `result` to the team-lead.

**Shape:** A specialist is a dispatched task, not a persistent process. The conductor invokes a specialist with a manifest entry; the specialist runs its specialties (worker + verifier, with retry loop), its consultants, its persona, and writes all rows to the arbitrator under `(session_id, team_id, specialist_id)`.

**Contract to team-lead:** Returns `{ result_id, passed, summary_fields }`. The team-lead reads details from the DB by `result_id` if needed.

### 5.7 Specialty (Worker + Verifier)

**Responsibility:** One worker/verifier pair focused on one cookbook artifact.

**Flow:**
1. Worker reads the artifact, produces structured findings via a dispatcher call.
2. Verifier reads the findings (NOT the worker's prompt), checks them for completeness via a dispatcher call, returns PASS or FAIL.
3. On FAIL: retry the worker up to 3 times with verifier feedback.
4. On 3 failures: escalate to the specialist (which may escalate to the team-lead).

**Isolation:** Worker and verifier are separate dispatcher calls with separate prompts. They never see each other's instructions.

### 5.8 Consultant

**Responsibility:** Cross-cutting review. Applies its lens across multiple specialty outputs.

**Shape:** Worker/verifier pair, same as a specialty, but its inputs are specialty *outputs*, not cookbook artifacts.

### 5.9 Persona

**Responsibility:** Translate raw findings into persona-voiced interpretations.

**Constraint:** Persona writes **only interpretation rows**. It produces no new findings. It is a translation layer, not a second opinion.

### 5.10 Observer

**Responsibility:** Forward dispatcher event streams to the arbitrator's `event` resource.

**Shape:** Each `Dispatcher.dispatch(...)` call is handed an `EventSink` that writes to the arbitrator. There is no separate observer process. Any UI that wants to "watch it think" subscribes to `arbitrator.subscribe_events(session_id, ...)`.

### 5.11 User Interface

**Responsibility:** Show the user what's happening and collect their input.

**Client contract:**
- Reads: `message`, `gate`, `event`, `result`, `finding`, `interpretation` via the arbitrator.
- Writes: `message` (chat to team-lead), `verdict` (gate response) via the arbitrator.
- Does **not** talk to the conductor directly.

**Selected via `--ui`:**
- `tui` — default. Textual or Rich-based terminal UI.
- `web` — Flask/FastAPI app with WebSocket subscription.
- `repl` — plain text prompt loop.
- `cc` — thin Claude Code wrapper (uses a CC session as the surface).
- `none` — no UI. Daemon/logs only. Useful for daemon-hosted sessions.

A session may have **multiple UIs attached** (e.g. a TUI for the operator and a web dashboard for a stakeholder) because all UIs are stateless arbitrator clients.

---

## 6. Data Model

### 6.1 Resource set

All resources (except `request`) carry `(session_id, team_id)` in their primary key or a unique constraint.

#### Core (from v2 arbitrator, carried forward)

| Resource | Purpose | Key fields |
|---|---|---|
| `session` | Pipeline run metadata | `session_id`, `initial_team_id`, `status`, `started_at`, `ended_at` |
| `state` | Persisted state tree node | `node_id`, `session_id`, `team_id`, `parent_node_id`, `state_name`, `status`, `entered_at`, `exited_at` |
| `message` | User ↔ team-lead speech | `message_id`, `session_id`, `team_id`, `direction`, `type` (question/answer/notification), `body`, `created_at` |
| `gate` | Paused checkpoint with options | `gate_id`, `session_id`, `team_id`, `category`, `options`, `verdict`, `created_at`, `resolved_at` |
| `result` | Specialist output envelope | `result_id`, `session_id`, `team_id`, `specialist_id`, `passed`, `summary_json`, `created_at` |
| `finding` | Individual issue within a result | `finding_id`, `result_id`, `kind`, `severity`, `body`, `source_artifact` |
| `interpretation` | Persona-voiced finding | `interpretation_id`, `finding_id`, `persona_id`, `body` |

#### Conductor-new

| Resource | Purpose | Key fields |
|---|---|---|
| `event` | Observer stream row | `event_id`, `session_id`, `team_id`, `agent_id`, `dispatch_id`, `sequence`, `kind`, `payload_json`, `emitted_at` |
| `task` | Conductor work queue | `task_id`, `session_id`, `team_id`, `kind`, `payload_json`, `status`, `enqueued_at`, `started_at`, `completed_at` |
| `request` | Inter-team request/response | `request_id`, `session_id`, `from_team`, `to_team`, `kind`, `input_json`, `status`, `response_json`, `parent_request_id`, `enqueued_at`, `in_flight_at`, `completed_at`, `timeout_at` |

#### Absorbed from project-storage-provider

`project-item`, `schedule`, `todo`, `issue`, `concern`, `dependency`, `decision` — all become first-class arbitrator resources with the same `(session_id, team_id)` key discipline. Schemas from the storage-provider spec carry over without material change.

### 6.2 Key rules (from `db-schema-design.md`)

- **No blob columns.** Summaries, narratives, and unstructured text are not stored in columns that won't be searched or joined.
- **No computed values.** Counts and totals come from queries.
- **No unstructured lists.** Lists become separate tables with one row per item.
- **Meaningful names.** `session_id` not `parent_id`; `creation_date` not `created_at` in project resources. `created_at` is retained for runtime infrastructure resources (event, task, request, message) where wall-clock semantics matter.
- **Project vocabulary.** No generic `component`/`entity` terms.

### 6.3 Indexes (minimum)

- `event(session_id, sequence)` — UI subscription ordering.
- `task(session_id, status, enqueued_at)` — main-loop queue pull.
- `request(session_id, status, enqueued_at)` — serial queue pull.
- `state(session_id, parent_node_id)` — state tree walks.
- `finding(result_id)` — detail queries.

---

## 7. Inter-Team Coordination

### 7.1 Model

Two teams running under the same conductor can read each other's rows freely via the arbitrator — status and progress are just queries. For **explicit request/response flows**, the `request` resource is the only sanctioned path.

### 7.2 Typed request kinds

Every request has a `kind` string (e.g. `pm.schedule.create`, `dev.specialist.run`). Each kind has a JSON schema for its `input` and another for its `response`. Schemas are registered with the arbitrator at conductor startup:

```python
arbitrator.register_request_kind(
    kind="pm.schedule.create",
    input_schema={...},
    response_schema={...},
    default_timeout_seconds=300,
)
```

Writes to `request.input_json` and `request.response_json` are validated against the registered schema. Malformed writes are rejected.

### 7.3 Handler registration

Each team's playbook declares which request kinds it handles:

```python
arbitrator.register_request_handler(
    team_id="pm",
    kind="pm.schedule.create",
    handler_state_node="handle_schedule_create",
)
```

When a request arrives with an unmatched kind for its `to_team`, the arbitrator fails it immediately with a `no_handler` error. The sender's team-lead sees the failure and handles it according to its state machine.

### 7.4 Serial queue funnel (deadlock prevention)

The arbitrator holds a **per-session serial queue** for root-level inter-team requests:

- At most one root-level request (one with `parent_request_id == null`) is in the `in-flight` state per session at any time.
- A new root-level request enters the queue as `pending`; the arbitrator moves it to `in-flight` when the previous root-level request completes.
- A request with a non-null `parent_request_id` **bypasses the queue** — it's part of servicing the parent and can't deadlock with it by construction.
- Every request has a mandatory `timeout_at`. On timeout the arbitrator marks the request `timeout`, advances the queue, and surfaces the failure to the sender.

**The queue is an implementation detail of the arbitrator.** Participants don't see it, don't set status fields, don't know whether their request is queued or in-flight. They call `arbitrator.request(...)` and `await_response(handle)`. The queue eliminates cyclic-wait deadlock by construction: there's never more than one pending conversation at a time.

### 7.5 Protocol errors

- **Timeout** — mandatory `timeout_at`, arbitrator enforces.
- **Schema violation** — rejected at write time.
- **No handler** — rejected at enqueue time.
- **Handler crash** — request marked `failed` with error detail; sender's team-lead handles per its retry policy.

---

## 8. Runtime Behavior

### 8.1 Session lifecycle

1. **Start.** `conductor start --session-id <uuid> --playbook <path>` creates the session, opens the arbitrator, loads the playbook, and invokes the initial state's entry actions.
2. **Run.** Main loop continues until the session reaches a terminal state declared by the playbook (`done`, `failed`, etc.) or is interrupted.
3. **Resume.** `conductor start --session-id <same-uuid>` with the same session ID reads the persisted state tree and resumes from the last completed node. Already-completed findings are not recomputed.
4. **Archive.** Completed sessions remain in the DB for forensic analysis. No implicit deletion.

### 8.2 State tree semantics

- The state tree is **tree-shaped, not list-shaped.** A team-lead dispatches a specialist → push child node. Specialist dispatches a specialty → push grandchild. Pops happen on completion in reverse order.
- Live tree is in-memory during a step; every push/pop is persisted to the `state` resource.
- On crash, restart reads the persisted tree and reconstructs in-memory state from the leaf nodes of the most recent active path.
- Completed subtrees are not re-executed on resume.

### 8.3 Dispatch lifecycle (one `claude -p` call)

1. Conductor builds prompt + agent definition + logical model name.
2. Conductor calls `dispatcher.dispatch(...)` with an `EventSink` pointing at the arbitrator.
3. Dispatcher:
   a. Spawns `claude -p` subprocess with the flags from §5.3.1.
   b. Closes stdin immediately.
   c. Reads stdout line-by-line, parses each line as JSON, writes each event to the sink.
   d. Reads stderr for diagnostics (non-fatal).
   e. On process exit: parses final result event, validates against `response_schema`, returns `DispatchResult`.
4. Conductor writes `result` / `finding` / `interpretation` rows based on the response.
5. Conductor advances the state tree.

**Wall-clock timeout:** Each dispatcher call has a hard timeout (configurable per agent). On timeout, the subprocess is terminated (SIGTERM, then SIGKILL), the call returns a typed error, and the team-lead's retry policy applies.

---

## 9. Host Integration

### 9.1 Terminal host (phase 1)

- User runs `conductor start ...` from a terminal.
- Conductor process is the terminal's child.
- TUI (default) runs in the same terminal.
- Closing the terminal terminates the conductor; next start with the same `--session-id` resumes.

This is the starting point. Simple, debuggable, tight feedback loop.

### 9.2 Daemon host (phase 2)

The existing `agentic-daemon` project gains the ability to host conductor jobs. See `~/projects/agentic-daemon/README.md`.

**Required daemon changes:**
- **Non-Swift job types.** Current daemon compiles and runs Swift `job.swift` scripts. Must also support Python service jobs (running `conductor start ...` as a subprocess with lifecycle management).
- **Service-mode jobs.** Current daemon runs jobs on a schedule. Must also support jobs that run until their session is complete, not on a schedule.
- **Client attach contract.** Structured protocol (unix socket candidate) for out-of-process clients (web UI, separate terminals) to attach to a running job. Clients talk through the arbitrator, not directly to the conductor — the attach contract is for delivering live output and input. Concrete protocol is a remaining open question.

**Job lifecycle:**
- One conductor process per session.
- Job status mirrors session status. There is no separate daemon-level job status concept.
- Daemon restarts: each job with an in-progress session is restarted and the session resumes from persisted state.

### 9.3 Future: native rewrites

Python is the prototype implementation. Hot paths (conductor, arbitrator, dispatcher) can be rewritten natively (Swift/Rust/Go) later, keeping the same contracts. The daemon itself is already Swift for this reason.

---

## 10. Configuration

### 10.1 Conductor CLI

```
conductor start
    --session-id <uuid>              (required; new or existing)
    --playbook <path>                (required; Python module path)
    [--ui tui|web|repl|cc|none]      (default: tui)
    [--dispatcher claude-code|local] (default: claude-code)
    [--storage sqlite|markdown]      (default: sqlite)
    [--host terminal|daemon]         (default: terminal)
    [--model-map <json>]             (logical → concrete model overrides)
    [--workdir <path>]               (where to resolve relative paths)

conductor status --session-id <uuid>
conductor stop --session-id <uuid>
conductor resume --session-id <uuid>
```

### 10.2 Agent definition files

Agents remain as markdown files in `plugins/<team>/agents/`. The conductor loads them at startup and, for `ClaudeCodeDispatcher`, builds the `--agents '<json>'` payload. Each agent file declares:

```markdown
---
name: interview-worker
logical_model: high-reasoning
allowed_tools: [Read, Grep]
---

# Interview Worker

<agent prompt body>
```

No `--agent <name>` escape hatch in the default path — every dispatch passes the explicit `--agents` JSON. Escape to a registered Claude Code agent is a separate, opt-in specialist type for cases where the full plugin/skill/MCP stack is the point.

### 10.3 Per-agent logical model config

Defined in the agent frontmatter (`logical_model:`). Concrete mapping lives in the dispatcher instance (see §5.3.3). Optional `--model-map` CLI flag overrides the default mapping at runtime.

---

## 11. Error Handling & Recovery

### 11.1 Categories

| Category | Who handles | Outcome |
|---|---|---|
| Worker schema violation | Specialty retry loop | Retry with verifier feedback, max 3, then escalate to specialist |
| Verifier says FAIL | Specialty retry loop | Same |
| Dispatcher subprocess crash / timeout | Dispatcher | Typed error → specialist retry policy |
| Specialist crash | Specialist orchestrator | Write `failed` state, escalate to team-lead |
| Team-lead judgment response invalid | Team-lead | Retry once, then gate user (category=error) |
| Inter-team request timeout | Arbitrator | Mark `timeout`, advance queue, sender handles |
| Arbitrator write failure | Calling component | Fatal; surfaces to team-lead, gates user |
| User interrupts | Session | Status = `interrupted`, resumable |

### 11.2 Crash recovery

- All state is persisted through the arbitrator. The conductor is stateless across restarts.
- Restart with the same `--session-id` reads the state tree, reconstructs in-memory state from the active path's leaf nodes, and resumes at the last incomplete node.
- Completed subtrees (already-written results, findings, interpretations) are not re-executed.
- In-flight dispatches at crash time are detected by the absence of a completion event; the owning state node is retried once on resume.

### 11.3 Gate escalation

When the team-lead can't make progress (exhausted retries, invalid responses, conflicting results), it emits a gate of category `error` with options for the user. User verdict determines next action: retry, skip, abort.

---

## 12. Migration Plan

### 12.1 Build order

1. **Walking skeleton: name-a-puppy, simplest path.**
   - Port `name-a-puppy` team to the new model.
   - One specialist (breed), one specialty, terminal UI, `ClaudeCodeDispatcher`, SQLite arbitrator.
   - Success: full session runs end-to-end without Claude Code.
2. **Full name-a-puppy.** Three specialists in parallel, state tree, judgment node for "any follow-up questions?", final aggregation.
3. **Cross-team flow.** Add a trivial second team to force the `request` resource, serial queue, and multi-team state tree into existence.
4. **Project-management team split.** Extract the PM specialist from the dev-team into its own team, using the new architecture as the interface.
5. **dev-team port.** Migrate the full dev-team workflow (interview/analysis/review/build/audit) to team-playbooks.

### 12.2 Existing workflow prose files

The current `interview.md`, `analysis.md`, `review.md`, `build.md`, `audit.md` workflow files are **conversational prose**. They are rewritten as Python team-playbooks **when their team ports**, not in a separate migration pass. No parallel maintenance of prose and Python representations.

### 12.3 Compatibility

- During the transition, the existing skill-based entry points (`/dev-team interview`, etc.) continue to work using the current (pre-conductor) implementation.
- A team is "ported" when its conductor-based entry point is stable and its prose workflow file is deleted.
- The old v2-spec arbitrator rows and new conductor arbitrator rows coexist in the same DB during migration (same schema, new columns are additive).

### 12.4 Architecture doc update

`docs/architecture.md` describes the **current state** of the system. It is rewritten to describe the conductor model **only after** the first production team is ported and stable. Not before.

---

## 13. Testing Strategy

### 13.1 Unit

- **State machines.** Each playbook's transitions are tested with mock judgment responses. Coverage: every declared transition fires at least once.
- **Dispatcher mocks.** Tests at the arbitrator and team-lead levels use a `MockDispatcher` that returns pre-canned responses.
- **Schema validation.** Round-trip tests for every resource schema and every request kind.

### 13.2 Integration

- **Full session replay.** A recorded session (events + requests + responses) can be replayed against the conductor to verify behavior across refactors.
- **Crash recovery.** Every test suite includes at least one "kill the conductor mid-dispatch and restart" test.
- **Multi-team coordination.** Tests covering the request queue (serial, timeout, bypass-via-parent).

### 13.3 End-to-end

- **Walking-skeleton session.** Full name-a-puppy run against `ClaudeCodeDispatcher` with a real `claude -p` subprocess. Verified by presence of result rows and absence of pending tasks.
- **Cost tracking.** Every test run records dispatcher call counts per logical model for regression on cost.

### 13.4 Out of scope for initial spec

- Load testing.
- Chaos testing beyond crash-recovery.
- Performance benchmarks beyond wall-clock per session.

---

## 14. Security

- **Subprocess input.** All inputs to `claude -p` (prompts, schemas, agents JSON) are built programmatically in Python and passed as CLI args. No shell interpolation of user text.
- **Storage isolation.** SQLite file lives under the workspace directory; permissions match the workspace.
- **Secrets.** No credentials in team-playbooks or agent files. Dispatcher-specific credentials (e.g. Anthropic API key for a future dispatcher) read from environment.
- **HTTP wrapper.** Binds to localhost by default. Remote exposure requires explicit configuration and is not in scope for the first release.

---

## 15. Remaining Open Questions

Captured for the implementation plan to resolve, not this spec:

1. **Unix socket contract for daemon-hosted client attach.** Structure of connect/subscribe/send for out-of-process clients talking to a daemon-hosted conductor.
2. **First `LocalDispatcher` target.** Which open-source model and runner. Maps to `high-reasoning` and `fast-cheap` logical tiers.
3. **Rate-limit and cost-visibility primitives.** How the conductor surfaces subscription headroom and running cost to the UI in real time.
4. **Playbook lint enforcement.** Whether "declarations not programs" is enforced mechanically, and how strict.
5. **Timeline visualization.** Deferred; session history in the DB makes it natural but not blocking.
6. **Resume-and-retry semantics for in-flight dispatches at crash time.** Spec says "retried once on resume" — needs concrete rules for partial results and event sequence numbers.

---

## 16. References

- **Research predecessor:** `docs/planning/2026-04-11-conductor-architecture.md` — brainstorming history and alternatives.
- **Terminology ancestor:** `docs/planning/2026-04-03-system-architecture-v2.md` — v2 DB-centric rearchitecture.
- **Current architecture:** `docs/architecture.md` — the current (pre-conductor) state.
- **Agentic daemon:** `~/projects/agentic-daemon/README.md` — the target phase-2 host.
- **DB schema rules:** `.claude/rules/db-schema-design.md`.
- **Directory conventions:** `.claude/rules/use-project-directories.md`.

---

## 17. Appendix: End-to-End Example (name-a-puppy)

### Scenario

User asks for puppy name suggestions. Session runs the `name-a-puppy` playbook.

### Trace

1. **Start.** `conductor start --session-id <new> --playbook playbooks/name_a_puppy.py --ui tui`
2. **Initial state.** `start` → entry action: send `notification` "Let's find a name for your puppy."
3. **Transition.** `start → gather_traits`.
4. **Judgment node.** `gather_traits` invokes `ask_next_question` judgment spec.
   - Dispatcher call: `claude -p --agents '{...}' --output-format stream-json --include-partial-messages --json-schema '{...}' --session-id <uuid> --model claude-sonnet-4-6`.
   - Events stream into the arbitrator as they arrive; TUI tails them live.
   - Response: `{ next_action: "ask", question: "What's the puppy's size?", next_state: "gather_traits" }`.
5. **Team-lead emits question.** `message` row written; TUI displays it.
6. **User answers.** TUI writes a `message` row; conductor enqueues an input task.
7. **Loop.** Repeat 4–6 until judgment response returns `next_state: dispatch_specialists`.
8. **Parallel dispatch.** State machine enters `dispatch_specialists`. Entry actions dispatch three specialists: `breed`, `lifestyle`, `temperament`. All three run concurrently; each emits its own events to the arbitrator.
9. **State tree.** Parent node `dispatch_specialists` has three children, one per specialist. Each child has grandchildren for specialty runs. All push/pops are persisted.
10. **Aggregation.** `aggregate` state reads all three result rows, builds a candidate list, dispatches a final judgment to rank them.
11. **Presentation.** `present` state emits a `notification` with the ranked names and a `gate` for "accept / reject / refine".
12. **User verdict.** Either transitions to `done` or loops back to `gather_traits`.
13. **Close.** `done` state writes session status, conductor exits cleanly.

### What was different from today

- Zero context accumulation in a Claude Code conversation.
- Three specialists ran concurrently without cross-contamination.
- Every dispatch was observable in the TUI in near-real-time.
- Crash-restart at any point would resume from the last completed state node.
- Swapping `ClaudeCodeDispatcher` for `LocalDispatcher` would be a one-flag change with no other code edits.
