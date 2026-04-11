# 2026-04-11 — Conductor Architecture (Headless Agentic Pipeline)

> **Status:** Research / planning — not a spec. Captures the output of a brainstorming session on 2026-04-11 and its continuation. Most of the original open questions are now resolved; a few remain and are listed at the end. A formal spec will follow in `docs/superpowers/specs/` once those remaining questions are closed.
>
> **Predecessor:** [`2026-04-03-system-architecture-v2.md`](./2026-04-03-system-architecture-v2.md) — started the DB-centric rearchitecture but still assumed the team-lead runs inside a Claude Code conversation. This doc picks up that thread and pushes the outer loop out of Claude entirely.
>
> **Brainstorm artifacts:** Visual diagrams produced during the sessions live under `.superpowers/brainstorm/<session-id>/content/` — see the "Visual references" section at the end.

## Context

The current dev-team model has the team-lead running inside the user's Claude Code conversation. This works fine for short runs but breaks on long ones:

- **Context accumulates in the conversation.** Questions, answers, tool outputs, subagent summaries, and script stdout all land in the main session and stay there. Tokens scale with length. Auto-compression is lossy.
- **Parallelism is awkward.** Specialists run inside the same conversation the team-lead is using to talk to the user. Dispatching several at once means the parent context sees the results of all of them.
- **Multi-team coordination has no natural home.** There's no shared data plane beyond "both teams reach into the same scripts." Inter-team comms becomes a messy design problem instead of falling out of the model.
- **Observability and context cost are in tension.** The only way for the user to "watch the LLM think" today is to have the LLM think inside their conversation — and pay for it in tokens.

The April 3 v2 doc started rearchitecting around a single database and DB-centric communication, but it kept the team-lead in the main conversation. The v2 terminology and disposition decisions are still valid foundations; the outer loop is where this doc diverges.

The pivot in one line: **the outer loop is a headless process, not a Claude Code session.** Intelligence at the edges (LLM workers, user), deterministic Python in the middle (conductor, arbitrator, state machines). Every LLM call is a one-shot dispatch with fresh context; nothing accumulates because there is no long-lived conversation.

## Core model

### Components

**Conductor** — long-running Python process, one per session. Hosted either by a terminal invocation or by the `agentic-daemon` service (see "Host" below). Owns the asyncio event loop. Dispatches LLM work through a pluggable **dispatcher** abstraction (see "Dispatcher" below). Writes everything through the arbitrator. Can run indefinitely; checkpoints come for free because all state is durable in the DB. The conductor is not itself an LLM — it's a scheduler, dispatcher, and event hub.

**Arbitrator + shared DB** — the one contract. Python library plus an optional thin HTTP wrapper. Every component (conductor, team-leads, workers, user interface, observer) reads and writes through this API. There is exactly one logical arbitrator per session, regardless of how many teams are running. The arbitrator absorbs the former project-storage-provider: project items, schedules, todos, issues, decisions, dependencies all become arbitrator resources. Backend is swappable via `--storage markdown|sqlite|...`; the arbitrator is the only component that knows or cares about the backend.

**Dispatcher** — LLM vendor abstraction layer. Encapsulates "run a prompt, get a structured response, stream events." Concrete implementations:
- `ClaudeCodeDispatcher` — the first and default. Invokes `claude -p` as a subprocess with `--agents '{...}'`, `--output-format stream-json`, `--include-partial-messages`, `--include-hook-events`, `--session-id <uuid>`, and optional `--json-schema <schema>` for structured output. Consumes the newline-delimited JSON event stream and forwards it to the arbitrator's `event` resource. Uses the user's existing Claude subscription (Max, Pro, etc.), not per-token API billing.
- `LocalDispatcher` (future) — wraps a locally-hosted open-source model (Ollama, vLLM, llama.cpp, etc.) with the same interface.
- Other vendor dispatchers as needed.

The dispatcher is the seam that makes LLM portability real. Everything above the dispatcher speaks in terms of "run agent X with prompt Y and get structured response Z" — what concrete model serves that request is a dispatcher concern.

**Team-leads** — state machine scaffolds with LLM-driven judgment nodes at specific points. Deterministic structure (legal states, legal transitions, entry actions, retry policy); the LLM is only invoked when the design says a judgment is needed. One team-lead per active team. The conductor invokes a team-lead per step, asking "given current state, what's next?" Team-leads do not hold long-lived state in memory — state lives as an ephemeral reference threaded through active participants, durably persisted in the DB.

**Specialists** — stateless dispatched tasks. Each specialist run is one or more dispatcher calls driven by the conductor. No persistent specialist process. Reads its manifest, dispatches specialty workers/verifiers/consultants/persona, writes results through the arbitrator, exits. The retry loop and orchestration are pure Python — no LLM is making that decision.

**Specialty workers, verifiers, consultants, persona** — LLM calls via the dispatcher. Fresh context each time. Output is structured findings, verifications, or interpretations written to the arbitrator. Isolated from each other — workers never see verifier instructions; consultants never see worker prompts.

**Observer** — the dispatcher's event stream. Every dispatch emits stream-json events (lifecycle, partial messages, tool-use, hook events). The dispatcher forwards each event to the arbitrator's `event` resource. Any UI or process can tail the event stream by subscribing to a session's events. Observability is one path, not two — no mixing of SDK callbacks with settings-file hook files.

**User interfaces** — TUI, web, REPL, thin Claude Code wrapper, or `none` (daemon mode, logs only). All are arbitrator *clients* — they read events and state, post messages and verdicts and chat. None talk to the conductor directly. The interface is selected at conductor start via `--ui tui|web|repl|cc|none`; TUI is the default.

### Terminology changes from v2

During the sessions, one rename landed: `specialty-team` → `specialty`. The "-team" part was implementation detail (a specialty is internally a worker/verifier pair), and the word "team" was getting overloaded with specialty-team / team-lead / plugin-as-team. Collapsing it removes the ambiguity.

Concrete renames:
- `specialty-team` → `specialty`
- `specialty-team-worker.md` → `specialty-worker.md`
- `specialty-team-verifier.md` → `specialty-verifier.md`
- `specialty-teams/` → `specialties/`
- `run_specialty_teams.py` → `run_specialties.py`
- Prose: "the project-manager specialist has 6 specialties" reads naturally.

A second clarification landed on **session vs. session-state**:
- **Session** — the data scope for a task. A set of rows across many tables all keyed by `session_id`. There may be a `session` object in code that encapsulates convenient accessors, but the session *is* the data. The arbitrator is who communication passes through, not the session.
- **State** — an ephemeral, tree-shaped reference threaded through active participants as they work. The whole run is a state machine; when a team-lead dispatches a specialist, that dispatch pushes a child state node; when a specialist dispatches a specialty, that pushes another. Pops happen when work completes. Live state tree is in memory; every push/pop and contents are also persisted to the DB so forensic postmortems can reconstruct what was happening at crash time. Archived sessions keep the full tree — history is not optional.

The old `workflow` term is replaced by **team-playbook**: the static authored definition of a team (state machine + judgment specs + manifest of specialists and specialties). "Workflow" was ambiguous with "runtime execution of a workflow." Team-playbook is the static asset; the session is the runtime instance.

Everything else from the v2 terminology table stands.

### Guiding principle

**Intelligence at the edges, deterministic plumbing in the middle.** User interfaces and LLM workers are the only places LLM thinking happens. Everything between them — conductor, arbitrator, dispatcher, specialist orchestrators, observers — is Python and SQL. No LLM is making decisions about whether to retry, what to store, how to route a message, or when to give up. Those are all script logic. LLMs are called at specific, constrained points where judgment is actually needed, and those points are enumerated in code.

## How a pipeline runs

### The conductor main loop

The conductor runs an 8-step cycle, forever, for the life of one session:

1. **Pick next work** — read pending tasks and events from the arbitrator queue for this session.
2. **Ask the team-lead state machine: what's next?** — load the current state node, hand it to the team's state machine. Returns actions plus next state.
3. **Execute actions in parallel** — dispatch specialists via the dispatcher, write gates for the user, update the DB. All async — no task blocks the loop.
4. **Stream events as they arrive** — dispatcher stream-json events become arbitrator `event` rows, tailed live by any UI listener.
5. **Persist results, transition state** — when a dispatch finishes, write result/finding/interpretation rows. Push or pop the state tree as appropriate.
6. **Handle user input** — chat messages and gate verdicts arrive via the arbitrator from any UI. Just another task type in the queue.
7. **Checkpoint** — every write is durable. Crash? Restart reads the persisted state tree and resumes from the last known node.
8. **Back to 1** — the conductor doesn't "finish" until the session is complete. It idles waiting for work until explicitly stopped or its session ends.

### Inside one dispatcher call

Zooming into what happens during a single `ClaudeCodeDispatcher` dispatch:

- **Conductor** builds the prompt, picks the agent, picks the logical model (see "Per-agent models" below), and hands it to the dispatcher.
- **Dispatcher** spawns `claude -p` as a subprocess using `asyncio.create_subprocess_exec(...)`, passing `--agents '{...}'` (inline agent JSON built from the project's agent markdown files), `--output-format stream-json`, `--include-partial-messages`, `--include-hook-events`, `--session-id <uuid>`, and `--json-schema <schema>` when a structured response is required. `--model` selects the concrete Claude model the logical name maps to.
- **Dispatcher** reads the subprocess stdout line-by-line. Each newline-delimited JSON event becomes an arbitrator `event` row with `session_id`, `team_id`, `agent_id`, and a monotonic sequence number.
- **UI listeners** (TUI, dashboard, tail) see events land in near-real-time by subscribing to the session's event stream. The user sees the LLM "thinking" with zero cost to the conductor's own context because the conductor isn't in a conversation.
- **Dispatcher** parses the final result message, validates it against the schema, and returns a structured response.
- **Conductor** writes `result` and `finding` rows, emits `dispatch.completed`, and advances the team-lead state machine.

Schema validation is first-class: a dispatcher call with a schema either returns a structurally-correct response or surfaces a validation error. A queried LLM cannot "ignore the request and hang everything up" because the contract is machine-checked at the boundary.

## Team-lead judgment model

### The question

A team-lead has to both iterate through specialists deterministically *and* make adaptive decisions (next interview question, conflict resolution, off-script user input). Purely state-machine is too rigid; purely LLM-loop defeats the whole point of moving the outer loop out of a conversation. What's the right mix?

### The answer: hybrid — state machine scaffold, LLM at specific nodes

**Deterministic parts** (pure Python, no LLM):

- Iterating through specialist manifests.
- Retry logic (N retries, then escalate).
- Legal transitions (state A can only go to B, C, or D).
- Writing results to the arbitrator.
- Pre-defined gates (e.g. "approve these findings before moving on").
- State tree management — pushes, pops, persistence.

**Judgment parts** (LLM calls, scoped to one question each, with a response schema):

- "Given the user's answers so far, what's the next interview question?"
- "Two specialists gave conflicting findings — how do I reconcile or escalate?"
- "Is the user ready to move on, or should I dig deeper?"
- "The user just asked something off-script — is that a new question, a clarification, or a veto?"
- "Given these findings, should I spin up a follow-up specialist I hadn't planned on?"
- "Write the persona-voiced summary of this section."

### Pattern

**The state machine decides *that* a decision needs to be made; the LLM decides *what* the decision is.**

A judgment node is a mini prompt template plus a constrained response schema. When the state machine reaches a judgment node, it calls the dispatcher with the template and schema, receives a validated response like `{ next_action, reasoning, next_state }`, validates that `next_state` is a legal successor of the current state, and transitions. Anything off-schema or targeting an illegal successor is rejected. The LLM stays in its lane.

### Why this shape

- **Bounded LLM surface.** Adding a judgment point is an explicit design decision by the team-playbook author — not ambient "whatever the LLM feels like."
- **Cheap by default.** Most transitions are free Python. The LLM only fires when the design says it should.
- **Testable.** State transitions unit-test cleanly with mock judgment responses.
- **Resumable.** The state tree is persisted. Restart the conductor, load the tree, continue — including mid-judgment if the LLM call was persisted.
- **Observable.** Each judgment call is an event stream in the arbitrator. The user can see "team-lead hit node X, asked this question, got this answer, transitioned from Y to Z" in real time.

### Different team-leads have different judgment ratios

- **Interview team-lead:** mostly judgment. Almost every step is adaptive — "what next?", "did we cover this enough?", "is this a follow-up or a new topic?"
- **Build team-lead:** mostly deterministic. Run specialists in order, aggregate, done.
- **Review / analysis / audit:** somewhere in between.

The scaffold shape is identical across all of them — just with different nodes marked as judgment-driven.

### Authoring: Python team-playbooks

Team-playbooks are authored in Python, following a **"declarations not programs"** convention:

1. A **state machine definition** — states, legal transitions, entry actions, retry policy. Data structures, not arbitrary control flow.
2. A set of **judgment specs** — prompt templates + response schemas — referenced by nodes that need them.
3. A **manifest** — specialists and specialties the team uses.

Why Python over YAML/DSL/JSON: Python gives us type checks, editor tooling, refactor support, and a shared language with the rest of the codebase — with zero translation layer. The risk is authors writing arbitrary imperative logic instead of declarations; convention discipline (and lint checks later if needed) keeps playbooks flat and data-shaped. If patterns emerge that would benefit from a more declarative format, we can add a layer that analyzes Python playbooks into a more declarative description — but only after we've built enough of them to see the shape.

## Data plane

One arbitrator, one DB, one contract. Inter-team communication is a side effect of shared tables — not a new feature to design.

### Ownership via `(session_id, team_id)`

Every row that belongs to a team carries both a `session_id` and a `team_id` in its primary key (or a composite unique constraint). This prevents cross-contamination when multiple teams share a session: Team A cannot overwrite Team B's rows by mistake, and queries naturally scope to the team that owns them. The two-party exception is the `request` resource below, which explicitly has `from_team` and `to_team` fields.

### Proposed arbitrator resource set

Carried from today's arbitrator (all now carry `(session_id, team_id)` ownership):
- `session` — a running pipeline instance
- `state` — persisted state tree nodes
- `message` — user ↔ team-lead
- `gate` — paused checkpoint with options
- `result` — specialist output envelope
- `finding` — individual issue within a result
- `interpretation` — persona-voiced finding

New for the conductor model:
- `event` — observer stream. Each dispatch emits rows; UIs subscribe. Includes dispatch lifecycle events, partial messages, tool-use events, hook events.
- `task` — conductor work queue. Team-lead actions to be executed. Conductor pulls, dispatches, marks complete.
- `request` — inter-team request/response. Two-party resource with `from_team`, `to_team`, `kind`, `input` (schema-validated), `status` (pending/in-flight/completed/failed/timeout), `response` (schema-validated), `timeout_at`, `parent_request_id`. See "Inter-team coordination" below.

Absorbed from project-storage-provider:
- `project-item`, `schedule`, `todo`, `issue`, `concern`, `dependency`, `decision`

These are no longer a separate provider — they're first-class arbitrator resources with the same API shape as everything else. The `--storage` flag becomes "the arbitrator's backend." Markdown remains the dev default; SQLite is the target for production long runs. **The arbitrator is the only component that knows or cares about the backend.**

### Inter-team coordination

Two teams running under the same conductor read and write the same tables. "Has the PM team created a schedule yet?" is a SQL read — no message bus needed. But when Team A specifically needs Team B to *do* something and return a result, we want an explicit mechanism.

**The `request` resource, with typed kinds and a serial funnel.**

- Every inter-team request has a **kind** (e.g. `pm.schedule.create`, `dev.specialist.run`). Each kind has a JSON schema for its `input` and another for its `response`. Schemas are enforced by the arbitrator on write.
- Requests have a mandatory `timeout_at`. No "the LLM wandered off and hung everything" failure mode.
- Handling is **deterministic on the receiver side**: the receiving team's playbook declares which request kinds it handles and what state machine node processes each. If no handler exists for a kind, the request is rejected immediately.
- The LLM's role in a request is constrained to the dispatcher call inside a judgment node, with a schema-validated response. The LLM cannot "decide" to ignore a request at the protocol level.

**Deadlock prevention: a serial queue funnel inside the arbitrator.**

At most one root-level inter-team request is in-flight per session at any time. The arbitrator holds a per-session queue; a new root-level request waits until the current one completes (or times out). Nested requests — ones that carry a `parent_request_id` pointing to an already-in-flight request — bypass the queue, because they're part of servicing the parent and can't deadlock with it by construction.

This is an **implementation detail inside the arbitrator**. Participants don't see the queue, don't set any status, don't know whether their request is queued or in-flight — they just call `arbitrator.request(...)` and await the response (or timeout). The queue is how the arbitrator avoids two pending inter-team conversations at once; eliminating two-at-once eliminates cyclic-wait deadlock by construction.

## Observer pattern

Not a disk-serialization hook layer. A dispatcher-forwarded event stream.

- The dispatcher invokes its concrete backend (subprocess, local model, whatever) and reads its event stream.
- For `ClaudeCodeDispatcher`, that event stream is `claude -p --output-format stream-json --include-partial-messages --include-hook-events`.
- Each event becomes an arbitrator `event` row with `session_id`, `team_id`, `agent_id`, and a monotonic sequence number.
- Any UI or process can tail the event stream by subscribing to a session's events (a database watch, a WebSocket, a file tail — whatever fits the UI).
- Hook events and tool-use events flow through the same stream as lifecycle events. One path, one table, no merge logic.

Realtime "watch it think" for the user: a free side effect of this architecture. No context cost, no special infrastructure, no trade-off.

## Host: where the conductor runs

The conductor is a Python process. How it gets started and managed depends on the scenario:

### Terminal-hosted (phase 1)

The user runs `conductor start --playbook=... --ui=tui` from a terminal. Conductor process is the child of the terminal. UI is a TUI in that terminal. Closing the terminal terminates the session — recoverable via crash-resume on next start, which reads the persisted state tree and picks up from the last completed node. This is the starting point: simple, debuggable, fast feedback loop.

### Daemon-hosted (phase 2)

The `agentic-daemon` project (user's existing Swift launchd daemon at `~/projects/active/agentic-daemon`) gains the ability to host conductor jobs:

- One conductor process per session, managed as a daemon job.
- Job lifecycle decoupled from terminal lifecycle — a user can start a job, close the terminal, open another, and reattach.
- External clients (web UI, another terminal, a remote tool) connect to the running job by reading the arbitrator state and event stream for that session. The conductor itself is not contacted directly; everyone talks through the arbitrator.
- Status of a job is a property of the session — the daemon doesn't need a separate "job status" concept. If the session is in-flight, the job is running; if the session is complete, the job ends.

Required additions to `agentic-daemon` for this role:
- Support for non-Swift job types (currently Swift-only).
- A service-mode job that runs until its session is complete, not on a recurring schedule.
- A structured contract for client attach/detach (unix socket is a candidate; needs design).

Phase 2 is deferred until phase 1 is working. The architecture is the same either way — only the host changes.

### Future: native rewrites

Python is the starting point. If/when hot paths prove slow enough to matter (the daemon itself is already Swift for exactly this reason), the conductor, arbitrator, and dispatchers can be rewritten natively (Swift, Rust, Go) while keeping the same contracts. The Python implementation is a prototype of the architecture, not the final word.

## Dispatcher: LLM portability and per-agent models

### Why the abstraction matters now

Two forces pushing on this:
1. The user's Claude subscription has weekly limits. Mixed-model work (cheap-and-fast for mechanical judgment, high-reasoning for hard calls) would make those limits go farther.
2. Open-source models are becoming credible for specific tasks. The ability to run, say, breed-name brainstorming against a local model while keeping high-reasoning Claude for the interview team-lead is a real want.

The dispatcher abstraction is the seam that makes both possible without rewriting the conductor.

### Per-agent logical model names

Every agent definition specifies a **logical model name** rather than a concrete model ID: `high-reasoning`, `fast-cheap`, `balanced`, `local`, etc. The dispatcher maps logical names to concrete models. This lets us:
- Change the concrete model for a role without editing every agent file.
- Use different concrete models in different dispatchers (Claude `sonnet-4.6` as `high-reasoning` in `ClaudeCodeDispatcher`, a local 70B model as `high-reasoning` in `LocalDispatcher`).
- Optimize per-run cost by picking the right logical tier for each call.

Model selection is an **explicit choice per agent, per call** — no implicit defaults that silently run every call at maximum cost.

### Agent definitions

Agents are authored as markdown files (today's `agents/` directory stays). The conductor loads them at startup and, for `ClaudeCodeDispatcher`, passes them to `claude -p` via `--agents '{...}'` (JSON built from the markdown). Markdown remains the authoring surface because it's ergonomic and diffable; the JSON conversion is a build step inside the dispatcher.

A specialist that genuinely needs a full Claude Code session (plugins, skills, MCP, the whole stack) can be invoked with `claude -p --agent <name>` against a pre-registered agent. This is an escape hatch for the rare case where the full-CC environment is the point — the default path is inline `--agents '{...}'` with only what the agent needs.

### Why not the Claude Agent SDK

The Python Claude Agent SDK (`claude_agent_sdk.query`, `ClaudeSDKClient`) was considered and rejected for the default dispatcher. It requires per-token API billing, which is incompatible with the user's Claude Max subscription. The Max subscription only covers `claude -p` subprocess usage. A future `AgentSDKDispatcher` could exist for users on per-token billing, but it is not the default.

## Resolved decisions (from the first-round open questions)

All ten questions from the first research draft are resolved. Captured here so future readers see the resolution history:

1. **User interface.** Pluggable. `--ui tui|web|repl|cc|none`. TUI is the default. All UIs are arbitrator clients.
2. **Build order.** `name-a-puppy` first (already exists, simplest surface) → add complexity until satisfied → PM team split → dev-team port.
3. **`claude -p` vs. Agent SDK.** `claude -p` is the primary dispatch mechanism. Agent SDK rejected due to billing model. `claude -p --agent <name>` remains as an escape hatch for full-CC specialists.
4. **Team-lead authoring format.** Python team-playbooks with "declarations not programs" convention.
5. **Migration of existing workflow prose.** Rewritten as team-playbooks when each team ports. No parallel maintenance of prose workflow files and Python playbooks.
6. **Conductor lifecycle.** Phase 1: terminal-hosted. Phase 2: hosted by `agentic-daemon` as per-session jobs.
7. **Existing `agents/` markdown files.** Kept as the authoring surface. Conductor loads them and passes via `--agents '{...}'`.
8. **Other reference teams.** Only `name-a-puppy` needs to move to start. Other teams migrate when their turn comes.
9. **Hook interop for the observer.** Subsumed by the stream-json observer: one event path via the dispatcher, one `event` table. No second source to merge.
10. **Inter-team coordination primitives.** `request` resource with typed kinds, input/response schemas, mandatory timeouts, deterministic handler registration, and an arbitrator-internal serial queue for deadlock prevention.

## Remaining open questions

A small set of things this doc deliberately leaves open:

1. **Unix socket contract for daemon-hosted conductor clients.** Phase-2 concern. Needs a structured attach/detach protocol so a web UI or remote tool can cleanly connect to a running job.
2. **First concrete open-source target for `LocalDispatcher`.** Which model, which runner (Ollama? vLLM? llama.cpp?), what the `high-reasoning`/`fast-cheap` mapping looks like in practice.
3. **Rate-limit and cost-visibility primitives.** With per-agent models and mixed dispatchers, we want real-time visibility into subscription headroom and running cost. Not blocking, but wanted before heavy production use.
4. **Lint / validation of team-playbooks.** "Declarations not programs" is a convention — do we enforce it mechanically? If so, how much?
5. **Timeline visualization.** Full session histories in the DB make product-development timeline charts natural. Deferred to a later pass.

## Alternatives considered

- **Per-team arbitrators.** Rejected. Early in the session we considered one arbitrator per team with cross-plugin dispatch machinery. Rejected: one contract, one arbitrator, inter-team comms is a side effect of shared tables — not a new mechanism to design.
- **Team-lead as the main Claude Code conversation.** The current model. Rejected because of context bloat on long runs, hard parallelism, and the observability/context tradeoff.
- **Claude Agent SDK as the primary dispatcher.** Rejected due to API billing incompatible with Claude Max. Could return as an optional dispatcher for users on per-token billing.
- **Pure LLM-driven team-lead.** An LLM that "figures out" what to do at every step, with no state machine scaffold. Rejected: unbounded surface, hard to test, and it re-creates the context-bloat problem we're trying to solve.
- **Pure state machine team-lead.** No LLM at all, every step deterministic. Rejected: can't handle interview flow, conflict resolution, off-script user input, or adaptive follow-up dispatch.
- **YAML / DSL for team-playbooks.** Considered; deferred in favor of Python with a "declarations not programs" convention. If patterns emerge that would benefit from a declarative format, a future pass can analyze Python playbooks into one.
- **Multi-session-per-conductor.** Considered; rejected. State management gets weird across sessions. One conductor per session. The concept of "sessions as steps in a larger plan" belongs to a roadmaps-v2 layer above the conductor, not inside it.
- **Plugin as the primary packaging unit.** Deferred. Skills / teams are the primary unit for now; plugins can wrap them later if marketplace distribution becomes important.
- **Timeouts + cycle-detection + dependency discipline for deadlock prevention.** Rejected in favor of the serial-queue funnel. One-at-a-time eliminates cyclic wait by construction; no graph analysis required.

## Followups

- **Formal spec** in `docs/superpowers/specs/YYYY-MM-DD-conductor-design.md` once the remaining open questions are resolved.
- **Implementation plan** in `docs/superpowers/plans/YYYY-MM-DD-conductor.md` referencing the spec.
- **First migration.** `name-a-puppy` ported to the new model. Expanded with extra complexity (cross-team request, multi-specialist sessions) until we're satisfied the architecture holds. Then the PM team split. Then the dev-team port.
- **`agentic-daemon` extensions.** Non-Swift job types + service-mode jobs + client attach contract, in support of phase-2 hosting.
- **Architecture doc update.** Once the new model ships, `docs/architecture.md` gets rewritten to describe it. Not before — `architecture.md` is the current-state doc, not aspirational.

## Visual references

Diagrams produced during the brainstorming sessions, preserved in `.superpowers/brainstorm/<session-id>/content/` while they remain on disk:

- `team-design.html` — pre-conductor framing. Team-as-self-enclosed-entity and the original 8-step execution flow.
- `conductor-model.html` — the conductor architecture (runtime topology), the conductor main loop, and the zoom-in on one dispatch call.

These are ephemeral — `.superpowers/brainstorm/` is gitignored. The content is captured in prose above; the HTML files are useful as long as they exist but this doc should be self-contained.
