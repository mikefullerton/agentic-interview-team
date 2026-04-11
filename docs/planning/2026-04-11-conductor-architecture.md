# 2026-04-11 — Conductor Architecture (Headless Agentic Pipeline)

> **Status:** Research / planning — not a spec. Captures the output of a brainstorming session on 2026-04-11. Open questions remain; see below. A formal spec will follow in `docs/superpowers/specs/` once those questions are resolved.
>
> **Predecessor:** [`2026-04-03-system-architecture-v2.md`](./2026-04-03-system-architecture-v2.md) — started the DB-centric rearchitecture but still assumed the team-lead runs inside a Claude Code conversation. This doc picks up that thread and pushes the outer loop out of Claude entirely.
>
> **Brainstorm artifacts:** Visual diagrams produced during the session live under `.superpowers/brainstorm/<session-id>/content/` — see the "Visual references" section at the end.

## Context

The current dev-team model has the team-lead running inside the user's Claude Code conversation. This works fine for short runs but breaks on long ones:

- **Context accumulates in the conversation.** Questions, answers, tool outputs, subagent summaries, and script stdout all land in the main session and stay there. Tokens scale with length. Auto-compression is lossy.
- **Parallelism is awkward.** Specialists run inside the same conversation the team-lead is using to talk to the user. Dispatching several at once means the parent context sees the results of all of them.
- **Multi-team coordination has no natural home.** There's no shared data plane beyond "both teams reach into the same scripts." Inter-team comms becomes a messy design problem instead of falling out of the model.
- **Observability and context cost are in tension.** The only way for the user to "watch the LLM think" today is to have the LLM think inside their conversation — and pay for it in tokens.

The April 3 v2 doc started rearchitecting around a single database and DB-centric communication, but it kept the team-lead in the main conversation. The v2 terminology and disposition decisions are still valid foundations; the outer loop is where this doc diverges.

The pivot in one line: **the outer loop is a terminal process, not a Claude Code session.** Intelligence at the edges (LLM workers, user), deterministic Python in the middle (conductor, arbitrator, state machines). Every LLM call is a one-shot `query()` with fresh context; nothing accumulates because there is no long-lived conversation.

## Core model

### Components

**Conductor** — long-running Python process, invoked from a terminal. Owns the asyncio event loop. Imports `claude_agent_sdk`. Dispatches LLM work as in-process `query()` calls. Writes everything through the arbitrator. Can run indefinitely; checkpoints come for free because all state is durable in the DB. The conductor is not itself an LLM — it's a scheduler, dispatcher, and event hub.

**Arbitrator + shared DB** — the one contract. Single API facade in front of a shared database. Every component (conductor, team-leads, workers, user interface, observer) reads and writes through this API. There is exactly one arbitrator in the system, regardless of how many teams are running. The arbitrator absorbs the former project-storage-provider: project items, schedules, todos, issues, decisions, dependencies all become arbitrator resources. Backend is swappable via `--storage markdown|sqlite|...`; the arbitrator is the only component that knows or cares about the backend.

**Team-leads** — state machine scaffolds with LLM-driven judgment nodes at specific points. Deterministic structure (legal states, legal transitions, entry actions, retry policy); LLM only called when the design says a judgment is needed. One team-lead per active team. The conductor invokes a team-lead per step, asking "given current state, what's next?" Team-leads do not hold long-lived state in memory — state lives in the DB.

**Specialists** — stateless dispatched tasks. Each specialist run is one or more SDK calls driven by the conductor. No persistent specialist process. Reads its manifest, dispatches specialty workers/verifiers/consultants/persona, writes results through the arbitrator, exits. The retry loop and orchestration are pure Python — no LLM is making that decision.

**Specialty workers, verifiers, consultants, persona** — LLM calls via Agent SDK `query()`. Fresh context each time. Output is structured findings, verifications, or interpretations written to the arbitrator. Isolated from each other — workers never see verifier instructions; consultants never see worker prompts.

**Observer** — in-process event callbacks registered with the SDK. Every dispatch emits events (started, token, tool-call, subagent-stop, finished). Callbacks write to the arbitrator `event` resource. Any UI or process can tail the event stream by subscribing to a session's events.

**User interfaces** — TUI, web, CLI, or thin Claude Code wrapper. All are arbitrator *clients* — they read events and state, post messages and verdicts and chat. None talk to the conductor directly. The specific interface is deferred (see open questions below).

### Terminology changes from v2

During the brainstorming session, one rename landed: `specialty-team` → `specialty`. The "-team" part was implementation detail (a specialty is internally a worker/verifier pair), and the word "team" was getting overloaded with specialty-team / team-lead / plugin-as-team. Collapsing it removes the ambiguity.

Concrete renames:
- `specialty-team` → `specialty`
- `specialty-team-worker.md` → `specialty-worker.md`
- `specialty-team-verifier.md` → `specialty-verifier.md`
- `specialty-teams/` → `specialties/`
- `run_specialty_teams.py` → `run_specialties.py`
- Prose: "the project-manager specialist has 6 specialties" (reads naturally)

Everything else from the v2 terminology table stands.

### Guiding principle

**Intelligence at the edges, deterministic plumbing in the middle.** User interfaces and LLM workers are the only places LLM thinking happens. Everything between them — conductor, arbitrator, specialist orchestrators, observers — is Python and SQL. No LLM is making decisions about whether to retry, what to store, how to route a message, or when to give up. Those are all script logic. LLMs are called at specific, constrained points where judgment is actually needed, and those points are enumerated in code.

## How a pipeline runs

### The conductor main loop

The conductor runs an 8-step cycle, forever:

1. **Pick next work** — read pending tasks and events from the arbitrator queue. Multiple teams and multiple sessions share one queue.
2. **Ask the team-lead state machine: what's next?** — load the session's current state, hand it to the team's state machine. Returns actions plus next state.
3. **Execute actions in parallel** — dispatch specialists via the SDK, write gates for the user, update the DB. All async — no task blocks the loop.
4. **Stream events as they arrive** — SDK callbacks fire in-process on token/tool-call/subagent boundaries. Each event becomes an arbitrator `event` row, tailed live by any UI listener.
5. **Persist results, transition state** — when a dispatch finishes, write result/finding/interpretation rows. Update the session state cursor.
6. **Handle user input** — chat messages and gate verdicts arrive via the arbitrator from any UI. Just another task type in the queue.
7. **Checkpoint** — every write is durable. Crash? Restart reads state and resumes.
8. **Back to 1** — the conductor doesn't "finish." It idles waiting for work until explicitly stopped.

### Inside one `query()` call

Zooming into what happens during a single SDK dispatch:

- **Conductor** builds the prompt and `ClaudeAgentOptions`: agent spec, allowed tools, hook callbacks, a forced `session_id=uuid` for correlation.
- **Conductor** starts `async for msg in query(prompt, options)`.
- **SDK** emits a `dispatch.started` event. Conductor writes it to the arbitrator.
- **SDK (streaming)** emits partial messages, token events, tool-call events. Each flushes to the arbitrator as `event` rows.
- **Hook callbacks** (`PreToolUse`, `PostToolUse`, `SubagentStop`, etc.) fire in-process. Python functions — no disk roundtrip. Each writes to the arbitrator with agent_id correlation.
- **UI listeners** (TUI, dashboard, tail) see events land in near-real-time. The user sees the LLM "thinking" with zero cost to the conductor's own context because the conductor isn't in a conversation.
- **SDK** emits the final result message. Conductor parses it, writes `result` and `finding` rows.
- **Conductor** emits `dispatch.completed`, advances the team-lead state machine.

Everything happens in **one Python process**. No subprocess spawn per task, no hook files on disk, no cross-process event serialization. The observer is literally a function pointer handed to the SDK.

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
- State cursor management.
- Reading/writing session state.

**Judgment parts** (LLM calls, scoped to one question each):

- "Given the user's answers so far, what's the next interview question?"
- "Two specialists gave conflicting findings — how do I reconcile or escalate?"
- "Is the user ready to move on, or should I dig deeper?"
- "The user just asked something off-script — is that a new question, a clarification, or a veto?"
- "Given these findings, should I spin up a follow-up specialist I hadn't planned on?"
- "Write the persona-voiced summary of this section."

### Pattern

**The state machine decides *that* a decision needs to be made; the LLM decides *what* the decision is.**

A judgment node is a mini prompt template plus a constrained response schema. When the state machine reaches a judgment node, it calls `query()` with the template, receives a schema-validated response like `{ next_action, reasoning, next_state }`, validates that `next_state` is a legal successor of the current state, and transitions. Anything off-schema or targeting an illegal successor is rejected. The LLM stays in its lane.

### Why this shape

- **Bounded LLM surface.** Adding a judgment point is an explicit design decision by the team-lead's author — not ambient "whatever the LLM feels like."
- **Cheap by default.** Most transitions are free Python. LLM only fires when the design says it should.
- **Testable.** State transitions unit-test cleanly with mock judgment responses.
- **Resumable.** The state cursor is a DB row. Restart the conductor, load the cursor, continue — including mid-judgment if the LLM call was persisted.
- **Observable.** Each judgment call is an event in the arbitrator. The user can see "team-lead hit node X, asked this question, got this answer, transitioned from Y to Z" in the stream.

### Different team-leads have different judgment ratios

- **Interview team-lead:** mostly judgment. Almost every step is adaptive — "what next?", "did we cover this enough?", "is this a follow-up or a new topic?"
- **Build team-lead:** mostly deterministic. Run specialists in order, aggregate, done.
- **Review / analysis / audit:** somewhere in between.

The scaffold shape is identical across all of them — just with different nodes marked as judgment-driven.

### Authoring

Authoring a team-lead means writing two things:

1. A **state machine definition** — states, legal transitions, entry actions, retry policy.
2. A set of **judgment specs** — prompt templates + response schemas — referenced by the nodes that need them.

Format for these is an open question (see below).

## Data plane

One arbitrator, one DB, one contract. Inter-team communication is a side effect of shared tables — not a new feature to design.

### Proposed arbitrator resource set

Carried from today's arbitrator:
- `session` — a running workflow instance
- `state` — session state cursor
- `message` — user ↔ team-lead
- `gate` — paused checkpoint with options
- `result` — specialist output envelope
- `finding` — individual issue within a result
- `interpretation` — persona-voiced finding

New for the conductor model:
- `event` — observer stream. Each LLM dispatch emits rows; UIs subscribe. Includes dispatch lifecycle events, token events, tool-use events, hook events.
- `task` — conductor work queue. Team-lead actions to be executed. Conductor pulls, dispatches, marks complete.

Absorbed from project-storage-provider:
- `project-item`, `schedule`, `todo`, `issue`, `concern`, `dependency`, `decision`

These are no longer a separate provider — they're first-class arbitrator resources with the same API shape as everything else. The `--storage` flag becomes "the arbitrator's backend." Markdown remains the dev default; SQLite is the target for production long runs. **The arbitrator is the only component that knows or cares about the backend.**

### Inter-team comms is free

Two teams running under the same conductor read and write the same tables. Team A doesn't need a message bus to reach Team B — it writes to the DB, Team B reads it. "Has the PM team created a schedule yet?" is a SQL query. Earlier design discussions about per-team arbitrators, cross-plugin dispatch, and session-to-session messaging all dissolve into "same tables, same arbitrator." The pushback: **implicit coordination via shared state is clean for status/progress reads but loose for request/response flows.** When Team A specifically needs Team B to do something and return a result, we want an explicit mechanism on top (probably a `task` row with team routing and a result correlation field). Still through the DB, but with clear semantics. Convention TBD — see open questions.

## Observer pattern

Not a disk-serialization hook layer. An in-process subscription pattern.

- The conductor wraps SDK dispatch with an event emitter.
- Hook callbacks passed via `ClaudeAgentOptions.hooks` are Python functions, called synchronously in-process by the SDK.
- Callbacks write to the arbitrator `event` resource.
- Any UI or process can tail the event stream by subscribing to a session's events (a database watch, a WebSocket, a file tail — whatever fits the UI).
- Claude Code `SubagentStop` / `PostToolUse` hooks from a settings file can optionally post events too (for cases where a specialist uses `claude -p` instead of SDK-native dispatch), but they are one **optional** source. Observability is not dependent on them.

Realtime "watch it think" for the user: a free side effect of this architecture. No context cost, no special infrastructure, no trade-off.

## Implementation mechanism — Agent SDK vs. `claude -p`

Research during the session (consulted Claude Code docs, Agent SDK Python docs, CLI reference) landed on these facts:

### `claude -p` (headless / print mode)

- Inherits hooks from discovered `.claude/settings.json` in cwd and `~/.claude/`. Runs the full skill/subagent/hook/MCP stack unless `--bare`.
- `--settings <path>` *merges* additional settings (does not replace). `--setting-sources user,project,local` controls which sources load.
- `--bare` skips auto-discovery entirely — clean slate, only loads what's explicitly passed.
- `--session-id <uuid>` forces a specific session ID. Useful for correlation.
- `--continue` / `--resume <id>` resumes previous sessions.
- `--output-format stream-json` + `--include-partial-messages` emits newline-delimited JSON events in real-time.
- No `CLAUDE_CONFIG_DIR` support (not documented). No `--hooks` flag — hooks come from settings files.
- Hooks that fire under `-p`: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PermissionRequest`, `Notification`. `SessionStart` / `SessionEnd` only fire via settings-file hooks (not SDK callbacks).
- Startup overhead ~500ms–1s per invocation (process spawn).

### Claude Agent SDK (Python / TypeScript)

- `query(prompt, options=ClaudeAgentOptions(...))` — one-shot async iterator. Fresh session per call. Options: `allowed_tools`, `hooks` (as in-process callbacks), `resume=session_id`, `mcp_servers`, `agents={}` (inline agent definitions), structured output.
- `ClaudeSDKClient()` — multi-turn client, maintains session state across calls, async context manager.
- Startup overhead ~50–100ms per call (library call, not process spawn).
- Hook delivery is in-process callback — no disk or network roundtrip.
- Streaming is a native async iterator of messages.
- Custom agents can be defined inline via `agents={}` in options — potentially replacing the current `agents/` markdown files.

### Decision direction

The conductor is **a Python process that imports the Agent SDK and dispatches `query()` calls** as its default mechanism. Hundreds of dispatches per pipeline run are realistic; process-spawn overhead makes `claude -p` the wrong default. Observer is a Python callback registered with the SDK, not a hook file on disk.

`claude -p` still earns a role where it's specifically wanted:
- A specialist that needs a full Claude Code session with plugins/skills/MCP auto-discovery.
- A user-facing "chat with a team-lead" mode that wraps an interactive Claude Code session.
- Any case where process isolation matters more than overhead.

When we do use `claude -p`, settings-file hooks can emit events that look identical to SDK-native events in the arbitrator — one event stream, two sources.

Still needs validation by a prototype: whether the SDK's `agents={}` option ergonomically replaces the `agents/` markdown files, or whether we keep markdown as the authoring surface and load-and-pass.

## Open questions

Deliberately captured rather than resolved — these are what the followup spec has to decide.

1. **User interface.** TUI (textual/rich), web dashboard (Flask/FastAPI + WebSocket), REPL (plain prompt), or thin Claude Code wrapper. Tradeoffs: information density, scriptability, implementation effort, and whether a Claude Code wrapper partly undoes the context-management win.
2. **First migration target.** Land the existing PM specialist split (dev-team → project-management team) on the new model as the first migration, or greenfield a small new team to validate the architecture end-to-end before touching existing code.
3. **`claude -p` role.** Pure SDK for internal workers with `claude -p` only for cases where a full Claude Code session is specifically wanted — or all-SDK, no `claude -p` at all?
4. **Team-lead authoring format.** How are state machines + judgment specs expressed on disk? YAML/JSON state machine + markdown prompt files? Pure Python? A small DSL? Tradeoff between authoring ergonomics and runtime flexibility.
5. **Migration path for existing workflows.** Today's workflow markdown files (interview, analysis, review, build, audit) are conversational. How do they translate to state machines + judgment specs? Ground-up rewrite or incremental conversion?
6. **Conductor lifecycle.** How is the conductor started, stopped, backgrounded, inspected? systemd, supervisord, terminal multiplexer, bespoke launcher? Not urgent, but needs an answer before the first user.
7. **Existing `agents/` markdown files.** The SDK's `agents={}` option lets you define agents inline. Keep markdown as the authoring surface and load it, or move to SDK-native `AgentDefinition` and retire the files?
8. **Other existing teams.** `name-a-puppy` and any future reference teams — migrate at the same time as the first production migration, or lag behind.
9. **Hook interop for the observer.** SDK callbacks are the primary path; Claude Code settings-file hooks can be a secondary source when `claude -p` is involved. Concrete design: how do events from both sources merge cleanly into one event stream per session without duplication?
10. **Inter-team coordination primitives.** The DB is the mechanism, but what *convention* do teams use when they need a response from another team (not just a status read)? A `task` row with team routing and a result correlation field? A request/response pattern layered on `message`? Needs a convention before any cross-team flow is built.

## Alternatives considered

- **Per-team arbitrators.** Rejected. Early in the session we considered one arbitrator per team with cross-plugin dispatch machinery. The user pushed back: one contract, one arbitrator, inter-team comms is a side effect of shared tables — not a new mechanism to design.
- **Team-lead as the main Claude Code conversation.** The current model. Rejected because of context bloat on long runs, hard parallelism, and the observability/context tradeoff.
- **`claude -p` as the primary dispatch mechanism.** Rejected. ~500ms–1s process startup per task, per-invocation config juggling, hook events serialized to disk/network. Fine for fewer than ~20 tasks per run; wrong for the 100s of tasks a real pipeline involves. `claude -p` remains valid for a narrow set of cases — it's just not the default.
- **Pure LLM-driven team-lead.** An LLM that "figures out" what to do at every step, with no state machine scaffold. Rejected: unbounded surface, hard to test, and it re-creates the context-bloat problem we're trying to solve.
- **Pure state machine team-lead.** No LLM at all, every step deterministic. Rejected: can't handle interview flow, conflict resolution, off-script user input, or adaptive follow-up dispatch.
- **Plugin as the primary packaging unit.** Deferred. The user explicitly set the plugin layer aside for now: distribution and marketplace value doesn't currently outweigh the development friction of plugin manifests and cache rebuilds. Skills / teams are the primary unit for now; plugins can wrap them later if marketplace distribution becomes important.

## Followups

- **Formal spec** in `docs/superpowers/specs/YYYY-MM-DD-conductor-design.md` once the open questions are resolved.
- **Implementation plan** in `docs/superpowers/plans/YYYY-MM-DD-conductor.md` referencing the spec.
- **First migration.** Either the PM team split (dev-team → project-management team) on the new model, or a greenfield validation team. Open question above.
- **Architecture doc update.** Once the new model ships, `docs/architecture.md` gets rewritten to describe it. Not before — `architecture.md` is the current-state doc, not aspirational.

## Visual references

Diagrams produced during the brainstorming session, preserved in `.superpowers/brainstorm/<session-id>/content/` while they remain on disk:

- `team-design.html` — pre-conductor framing. Team-as-self-enclosed-entity and the 8-step execution flow.
- `conductor-model.html` — the conductor architecture (runtime topology), the conductor main loop, and the zoom-in on one `query()` call.

These are ephemeral — `.superpowers/brainstorm/` is gitignored. The content is captured in prose above; the HTML files are useful as long as they exist but this doc should be self-contained.
