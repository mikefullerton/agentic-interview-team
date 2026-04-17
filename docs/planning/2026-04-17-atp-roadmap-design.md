# 2026-04-17 — atp Roadmap System Design

> **Status:** Design summary. Captures the output of a brainstorming session on 2026-04-17. The companion plan lives at `~/.claude/plans/the-more-i-gentle-pie.md`. A formal implementation plan will follow in `docs/planning/2026-04-17-atp-roadmap-plan.md`.
>
> **Depends on:** [`2026-04-11-conductor-architecture.md`](./2026-04-11-conductor-architecture.md) — atp sits **above** the conductor as the "roadmaps-v2 layer" that doc anticipates (line 305).
>
> **Supersedes:** the flat `project-item / todo / milestone / schedule` sketch in the conductor doc's proposed resource set. That sketch was a preview of the structured roadmap described here.

## Context

atp (Agentic Team Plugin) is a two-phase system for building software projects:

- **Phase 1 — planning:** an interview team-lead plus specialists (in planning mode) build a roadmap by guided questioning. Output: a structured plan that can be re-read and executed later.
- **Phase 2 — execution:** the roadmap is walked; primitives are dispatched to build-teams in parallel; progress is observable, resumable, and modifiable mid-flight.

The predecessor is the paused `~/projects/paused/roadmaps` project. Its lessons carry forward (file-based artifacts, state-as-events, deterministic next-step selection, YAML-frontmatter metadata); its limits are fixed here (flat step list → tree+DAG graph; no parallelism → dependency-aware dispatch; no insertion → lazy HTN-style decomposition).

This document specifies the data model: the roadmap graph, the set of arbitrator resources it joins, and the SQLite schema backing them. Component behavior (conductor main loop, team-lead state machines, specialist planning-mode contract) is specified elsewhere.

## Core model — one graph, two projections

Every roadmap is a **single graph** of plan nodes. Each node carries two edge kinds:

- **`parent_id`** — tree edge. Defines the hierarchical outline a human or LLM reads ("app → feature → theme-picker"). Exactly one parent per node.
- **`depends_on[]`** — DAG edges. Define execution ordering with parallelism. Zero or more prerequisites per node.

The same nodes form two projections:

- **Tree projection** (follow `parent_id` only) — used by planning phase and for human review. Renderable as a nested markdown outline.
- **DAG projection** (follow `depends_on` only) — used by execution phase. Topological sort yields a partial order; independent subtrees run in parallel.

There is no separate "execution graph." Execution reads the same rows through a different lens.

### Node kinds (HTN-inspired)

| `node_kind` | Meaning | Execution |
|---|---|---|
| `compound` | Decomposes into children by invoking a specialist's planning-mode worker. Can re-decompose mid-execution if new information arrives. | Completes when all of its children complete. |
| `primitive` | Directly actionable. Dispatches to a build-team in execution phase. | Runs to `done` / `failed`. |

Lazy decomposition solves on-the-fly insertion: a compound node isn't "frozen" after planning — a downstream finding can trigger a re-decomposition, producing new children without patching a committed DAG.

### Addressing

- **Canonical ID:** stable slug or UUID (`node_id`). Never reused, never renumbered on insertion.
- **URL-style paths** (`agentic-roadmap://markdown-editor/app/feature/theme-picker`) and **dotted outline numbers** (`1.2.3`) are **rendered for display only**, computed from `parent_id` + `position` at read time. Not stored. Insertion and renaming do not cascade.
- **Position:** fractional index (REAL). New siblings pick a position between neighbors; no global renumber is ever needed.

## Five streams and the join key

The graph is one stream of five. Each stream has its own natural shape; forcing them into a single table would fight those shapes. They are linked at query time via a shared `plan_node_id` column.

| Stream | Resources | Shape | Scope |
|---|---|---|---|
| 1. Roadmap | `roadmap`, `plan_node`, `node_dependency`, `node_state_event` | Tree + DAG + append-only log | **Project-wide** — survives across sessions |
| 2. Session & runtime | `session`, `session_property`, `team`, `state`, `task` | Flat + call stack | Per-session |
| 3. Transcript | `message`, `gate`, `gate_option`, `verdict`, `interpretation` | Chronological | Per-session |
| 4. Inter-team requests | `request` | Typed-kind queue | Per-session |
| 5. Observer | `event`, `dispatch`, `attempt` | Firehose + retry protocol | Per-session |

**Plus** — `result`, `finding`, `artifact` (specialist outputs) and `concern`, `decision` (cross-cutting annotations), all optionally linked by `plan_node_id`. And `body` — a single side-table that isolates all narrative content per the DB-design rules.

### `plan_node_id` as the join key

Every row in streams 2–5 (except session-level metadata) carries an **optional `plan_node_id`**. This gives:

- **Attribution** — "who said what, when, about which plan node."
- **Cross-stream filtering** — "show me everything about `/app/feature/theme-picker`" returns messages + events + requests + state transitions + findings in a single query (`UNION ALL` over stream tables, filtered by `plan_node_id`).
- **Per-node observability** — "node X had 3 dispatches, 12 tool-uses, 1 unresolved conflict, 2 user messages."
- **Replay** — reconstruct the meeting that produced any node.

### Scope boundaries

- **Roadmap state** (`node_state_event`) = lifecycle across sessions. "Is this node planned / ready / running / done?" Answers what the project has achieved.
- **Session state** (`state`) = ephemeral dispatch call stack inside one session, persisted for crash-resume. "Who called whom right now?" Answers what's happening this instant.

The two are distinct resources with distinct lifecycles. They cross-reference via `session_id` on `node_state_event` (which session caused this transition) and `plan_node_id` on `state` (which roadmap node this dispatch addresses).

## Architecture placement

```
                    ┌─────────────────────────────┐
                    │    atp (roadmaps-v2)        │  ← reads roadmap stream,
                    │    - walks DAG              │    spawns conductor sessions
                    │    - decides when to run    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Conductor (per session)  │  ← from 2026-04-11
                    │    - 8-step main loop       │    conductor-architecture.md
                    │    - dispatches teams       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Arbitrator (the API)     │  ← single contract;
                    │    - resources above        │    everyone reads/writes here
                    │    - event bus              │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Storage-provider (backend) │  ← pluggable;
                    │  SQLite (default)           │    only arbitrator talks to it
                    └─────────────────────────────┘
```

**Arbitrator vs storage-provider.** The conductor doc's "arbitrator absorbed project-storage-provider" refers to the **external** project-storage CRUD API (that specialists called directly) going away. The **internal** storage-provider — the arbitrator's pluggable persistence backend — remains. Participants see only the arbitrator; the arbitrator delegates to the storage-provider.

## Schema

SQLite. Single database per workspace at `.atp/atp.db` (path configurable). All `session_id`, `team_id`, `plan_node_id`, `node_id` are TEXT. All `*_date` columns are DATETIME. Foreign keys are enforced (`PRAGMA foreign_keys = ON`).

### Roadmap (project-scoped)

```sql
CREATE TABLE roadmap (
  roadmap_id          TEXT PRIMARY KEY,
  title               TEXT NOT NULL,
  creation_date       DATETIME NOT NULL,
  modification_date   DATETIME NOT NULL
);

CREATE TABLE plan_node (
  node_id             TEXT PRIMARY KEY,
  roadmap_id          TEXT NOT NULL,
  parent_id           TEXT,                     -- NULL = root
  position            REAL NOT NULL,            -- fractional index
  node_kind           TEXT NOT NULL,            -- compound | primitive
  title               TEXT NOT NULL,
  specialist          TEXT,                     -- domain owner
  speciality          TEXT,                     -- leaf owner
  creation_date       DATETIME NOT NULL,
  modification_date   DATETIME NOT NULL,
  FOREIGN KEY (roadmap_id) REFERENCES roadmap(roadmap_id),
  FOREIGN KEY (parent_id)  REFERENCES plan_node(node_id)
);

CREATE TABLE node_dependency (
  dependency_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id             TEXT NOT NULL,            -- dependent
  depends_on_id       TEXT NOT NULL,            -- prerequisite
  creation_date       DATETIME NOT NULL,
  UNIQUE (node_id, depends_on_id),
  FOREIGN KEY (node_id)       REFERENCES plan_node(node_id),
  FOREIGN KEY (depends_on_id) REFERENCES plan_node(node_id)
);

CREATE TABLE node_state_event (
  event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id             TEXT NOT NULL,
  session_id          TEXT,                     -- which session drove this transition
  event_type          TEXT NOT NULL,            -- planned|ready|running|done|failed|superseded
  actor               TEXT NOT NULL,
  event_date          DATETIME NOT NULL,
  FOREIGN KEY (node_id) REFERENCES plan_node(node_id)
);
```

### Session & runtime

```sql
CREATE TABLE session (
  session_id              TEXT PRIMARY KEY,
  playbook                TEXT NOT NULL,        -- e.g. atp-plan, atp-execute
  roadmap_id              TEXT,                 -- what this session is working on
  plan_node_id            TEXT,                 -- anchor node
  host                    TEXT NOT NULL,        -- terminal | daemon
  pid                     INTEGER,              -- conductor PID; NULL if not running
  status                  TEXT NOT NULL,        -- starting|running|idle|completed|failed|aborted
  ui_mode                 TEXT NOT NULL,        -- tui|web|repl|cc|none
  last_task_id            TEXT,                 -- crash-resume cursor
  last_state_id           TEXT,                 -- crash-resume cursor
  last_event_sequence     INTEGER,              -- observer tail cursor
  creation_date           DATETIME NOT NULL,
  modification_date       DATETIME NOT NULL,
  completion_date         DATETIME,
  FOREIGN KEY (roadmap_id)   REFERENCES roadmap(roadmap_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE session_property (
  session_id          TEXT NOT NULL,
  property_key        TEXT NOT NULL,
  property_value      TEXT NOT NULL,
  modification_date   DATETIME NOT NULL,
  PRIMARY KEY (session_id, property_key),
  FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE team (
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  team_playbook       TEXT NOT NULL,
  team_role           TEXT NOT NULL,            -- interview|analysis|build|executor|...
  status              TEXT NOT NULL,            -- active|paused|completed
  creation_date       DATETIME NOT NULL,
  modification_date   DATETIME NOT NULL,
  PRIMARY KEY (session_id, team_id),
  FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE state (
  state_id            TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  parent_state_id     TEXT,                     -- call-stack tree edge
  plan_node_id        TEXT,                     -- which roadmap node this addresses
  state_name          TEXT NOT NULL,            -- node in the team's state machine
  actor               TEXT NOT NULL,            -- team-lead|specialist|speciality|persona
  status              TEXT NOT NULL,            -- pending|running|waiting|done|failed|cancelled
  entry_date          DATETIME NOT NULL,
  exit_date           DATETIME,
  FOREIGN KEY (session_id)      REFERENCES session(session_id),
  FOREIGN KEY (parent_state_id) REFERENCES state(state_id),
  FOREIGN KEY (plan_node_id)    REFERENCES plan_node(node_id)
);

CREATE TABLE task (
  task_id             TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  state_id            TEXT,                     -- state node that enqueued this
  task_kind           TEXT NOT NULL,            -- dispatch|request|gate-await|persist|...
  status              TEXT NOT NULL,            -- queued|in-flight|completed|failed|cancelled
  scheduled_date      DATETIME,
  started_date        DATETIME,
  completion_date     DATETIME,
  FOREIGN KEY (session_id) REFERENCES session(session_id)
);
```

### Transcript

```sql
CREATE TABLE message (
  message_id          TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  plan_node_id        TEXT,
  from_actor          TEXT NOT NULL,            -- user|team-lead|specialist|speciality
  to_actor            TEXT NOT NULL,
  message_type        TEXT NOT NULL,            -- question|answer|notification
  persona             TEXT,
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE gate (
  gate_id             TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  plan_node_id        TEXT,
  gate_category       TEXT NOT NULL,            -- flow|error|conflict
  status              TEXT NOT NULL,            -- open|answered|expired
  creation_date       DATETIME NOT NULL,
  verdict_date        DATETIME,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE gate_option (
  option_id           TEXT PRIMARY KEY,
  gate_id             TEXT NOT NULL,
  option_label        TEXT NOT NULL,
  position            INTEGER NOT NULL,
  FOREIGN KEY (gate_id) REFERENCES gate(gate_id)
);

CREATE TABLE verdict (
  verdict_id          TEXT PRIMARY KEY,
  gate_id             TEXT NOT NULL,
  option_id           TEXT NOT NULL,
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (gate_id)   REFERENCES gate(gate_id),
  FOREIGN KEY (option_id) REFERENCES gate_option(option_id)
);

CREATE TABLE interpretation (
  interpretation_id   TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  finding_id          TEXT NOT NULL,
  plan_node_id        TEXT,
  persona             TEXT NOT NULL,
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (finding_id)   REFERENCES finding(finding_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
```

### Inter-team requests

```sql
CREATE TABLE request (
  request_id              TEXT PRIMARY KEY,
  session_id              TEXT NOT NULL,
  from_team               TEXT NOT NULL,
  to_team                 TEXT NOT NULL,
  parent_request_id       TEXT,                 -- nested requests bypass serial queue
  plan_node_id            TEXT,
  request_kind            TEXT NOT NULL,        -- planning.decompose-node|execution.realize-node|...
  status                  TEXT NOT NULL,        -- pending|queued|in-flight|completed|failed|timeout
  timeout_date            DATETIME NOT NULL,
  creation_date           DATETIME NOT NULL,
  completion_date         DATETIME,
  FOREIGN KEY (session_id)        REFERENCES session(session_id),
  FOREIGN KEY (parent_request_id) REFERENCES request(request_id),
  FOREIGN KEY (plan_node_id)      REFERENCES plan_node(node_id)
);
```

### Observer + dispatch + retry protocol

```sql
CREATE TABLE dispatch (
  dispatch_id         TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  state_id            TEXT,                     -- state node that initiated the dispatch
  plan_node_id        TEXT,
  agent_kind          TEXT NOT NULL,            -- speciality-worker|speciality-verifier|
                                                -- consulting-worker|consulting-verifier|
                                                -- persona|judgment|team-lead-judgment
  agent_name          TEXT NOT NULL,
  logical_model       TEXT NOT NULL,            -- high-reasoning|fast-cheap|balanced|local
  concrete_model      TEXT,                     -- resolved at dispatch time
  status              TEXT NOT NULL,            -- pending|running|completed|failed|timeout
  schema_valid        INTEGER NOT NULL DEFAULT 0,  -- 0/1: did response pass schema
  start_date          DATETIME NOT NULL,
  end_date            DATETIME,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE attempt (                           -- worker-verifier retry cycle
  attempt_id              TEXT PRIMARY KEY,
  result_id               TEXT NOT NULL,
  session_id              TEXT NOT NULL,
  attempt_kind            TEXT NOT NULL,        -- speciality | consulting
  owner_name              TEXT NOT NULL,        -- speciality name or consulting-team name
  attempt_number          INTEGER NOT NULL,     -- 1..3
  worker_dispatch_id      TEXT NOT NULL,
  verifier_dispatch_id    TEXT,                 -- NULL until verifier runs
  verdict                 TEXT,                 -- pass|fail|verified|not-applicable|pending
  failure_reason          TEXT,                 -- short queryable reason
  start_date              DATETIME NOT NULL,
  end_date                DATETIME,
  UNIQUE (result_id, attempt_kind, attempt_number),
  FOREIGN KEY (worker_dispatch_id)   REFERENCES dispatch(dispatch_id),
  FOREIGN KEY (verifier_dispatch_id) REFERENCES dispatch(dispatch_id)
);

CREATE TABLE event (
  event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id          TEXT NOT NULL,
  team_id             TEXT,
  agent_id            TEXT,
  plan_node_id        TEXT,
  dispatch_id         TEXT,
  sequence            INTEGER NOT NULL,         -- monotonic per session
  event_kind          TEXT NOT NULL,            -- lifecycle|partial-message|tool-use|hook
  event_subtype       TEXT,
  event_date          DATETIME NOT NULL,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (dispatch_id)  REFERENCES dispatch(dispatch_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
```

### Results & artifacts

```sql
CREATE TABLE result (
  result_id           TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  specialist          TEXT NOT NULL,
  speciality          TEXT,
  plan_node_id        TEXT,
  state_id            TEXT,
  status              TEXT NOT NULL,            -- pass|fail|partial
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE finding (
  finding_id          TEXT PRIMARY KEY,
  result_id           TEXT NOT NULL,
  plan_node_id        TEXT,
  finding_kind        TEXT NOT NULL,            -- gap|recommendation|concern
  severity            TEXT NOT NULL,            -- low|medium|high|critical
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (result_id)    REFERENCES result(result_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE artifact (
  artifact_id         TEXT PRIMARY KEY,
  session_id          TEXT NOT NULL,
  team_id             TEXT NOT NULL,
  plan_node_id        TEXT,
  result_id           TEXT,
  artifact_kind       TEXT NOT NULL,            -- code|doc|report|config
  artifact_path       TEXT NOT NULL,            -- real files stay files
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (session_id)   REFERENCES session(session_id),
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
```

### Annotations (cross-cutting)

```sql
CREATE TABLE concern (
  concern_id          TEXT PRIMARY KEY,
  session_id          TEXT,
  plan_node_id        TEXT,
  raised_by           TEXT NOT NULL,
  title               TEXT NOT NULL,
  severity            TEXT NOT NULL,
  status              TEXT NOT NULL,            -- open|addressed|wontfix
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE decision (
  decision_id         TEXT PRIMARY KEY,
  session_id          TEXT,
  plan_node_id        TEXT,
  title               TEXT NOT NULL,
  decided_by          TEXT NOT NULL,
  creation_date       DATETIME NOT NULL,
  FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
```

### Body side-table

Narrative content — node descriptions, message bodies, finding prose, rationale, persona interpretations — lives here, not in the primary rows. This keeps the queryable rows lean and honors the `.claude/rules/db-schema-design.md` prohibition on blob columns by isolating blobs to one explicit place.

```sql
CREATE TABLE body (
  owner_type          TEXT NOT NULL,            -- plan_node|message|finding|interpretation|
                                                -- concern|decision|gate|request|...
  owner_id            TEXT NOT NULL,
  body_format         TEXT NOT NULL,            -- markdown|plain|json
  body_text           TEXT NOT NULL,
  modification_date   DATETIME NOT NULL,
  PRIMARY KEY (owner_type, owner_id)
);
```

### Indexes

```sql
-- Roadmap traversal
CREATE INDEX idx_plan_node_tree  ON plan_node(roadmap_id, parent_id, position);
CREATE INDEX idx_node_dep_from   ON node_dependency(node_id);
CREATE INDEX idx_node_dep_to     ON node_dependency(depends_on_id);
CREATE INDEX idx_nse_latest      ON node_state_event(node_id, event_date DESC);

-- Session runtime
CREATE INDEX idx_state_tree      ON state(session_id, parent_state_id);
CREATE INDEX idx_task_queue      ON task(session_id, status, scheduled_date);
CREATE INDEX idx_request_queue   ON request(session_id, status, timeout_date);

-- Observer
CREATE INDEX idx_event_tail      ON event(session_id, sequence);
CREATE INDEX idx_dispatch_session ON dispatch(session_id, start_date);
CREATE INDEX idx_dispatch_agent  ON dispatch(agent_kind, agent_name);
CREATE INDEX idx_attempt_result  ON attempt(result_id, attempt_number);

-- plan_node_id cross-stream joins
CREATE INDEX idx_msg_node        ON message(plan_node_id);
CREATE INDEX idx_req_node        ON request(plan_node_id);
CREATE INDEX idx_event_node      ON event(plan_node_id);
CREATE INDEX idx_state_node      ON state(plan_node_id);
CREATE INDEX idx_result_node     ON result(plan_node_id);
CREATE INDEX idx_finding_node    ON finding(plan_node_id);
```

## Why concerns and decisions are separate tables (not plan-node kinds)

A concern ("this feature may conflict with GDPR") or a decision ("chose SwiftUI over AppKit because...") looks at first like something that could be a `plan_node` row with `node_kind ∈ {concern, decision}`. Rejected because the shapes genuinely differ:

| Aspect | Plan node | Concern | Decision |
|---|---|---|---|
| Gets decomposed | Yes (compound) | No | No |
| Gets executed | Yes (primitive) | No | No |
| Has dependencies | Yes | No | No |
| Lifecycle | planned → ready → running → done | open → addressed → wontfix | logged once |
| Parent semantics | Sub-plan of | Attached to | Attached to |

Collapsing them would require every executor query to carry `WHERE node_kind IN ('compound','primitive')`, `node_state_event` would mix two incompatible event-type enums, and `parent_id` would carry two semantically different meanings. Concerns and decisions are **annotations on the graph**, not nodes in it — the same relationship every non-roadmap stream has. They link via `plan_node_id`.

## Integration with the conductor

atp is the layer **above** the conductor. An atp invocation consults the roadmap, decides what work to launch, and invokes the conductor with a suitable playbook. The conductor handles one session at a time; multi-team parallelism inside a session is already in the conductor's design.

### Phase 1 — planning

```
atp plan <roadmap-id>
  → conductor start --playbook=atp-plan --roadmap=<id> --plan-node=<id?>
    → interview team-lead runs
      → specialists dispatched in planning mode
        → write plan_node rows + node_dependency edges
        → recurse into compound children lazily
    → session completes
  → roadmap graph updated
```

Specialists write their subtree's structure and dependencies — they know, for example, that `signing` depends on `team-account`. The DAG projection emerges from specialist domain knowledge, not a separate wiring pass.

### Phase 2 — execution

```
atp execute <roadmap-id>
  → conductor start --playbook=atp-execute --roadmap=<id>
    → executor team-lead walks the DAG projection
      → for each node with all deps done:
        → open inter-team request (kind: execution.realize-node)
        → build-team realizes the primitive
        → writes node_state_event → done
      → compound nodes may re-decompose if new findings surface
    → session completes when all roadmap primitives are done
```

**Session scope** — default is one conductor session per `atp execute` run. The executor team handles the full DAG; build-teams run in parallel via `request`. Alternative scopes (one session per primitive, hybrid batching) are supported by the schema but deferred as a future refinement.

### Request kinds

The `request.request_kind` column holds namespaced identifiers. Initial set:

- `planning.decompose-node` — ask another team to expand a compound plan node.
- `planning.review-subtree` — ask another team to review a planning subtree.
- `execution.realize-node` — ask a build-team to realize a primitive.
- `execution.verify-node` — ask a review team to verify a realized primitive.

Each kind has a JSON schema for its `input` and `response` (schemas live alongside team playbooks; enforced by the arbitrator on write per the conductor doc).

### Multi-team coordination

The conductor doc already describes everything needed: `(session_id, team_id)` ownership, `request` with typed kinds and arbitrator-internal serial queue for deadlock prevention, nested requests bypassing the queue. No new coordination primitives introduced here.

## Relationship to the paused roadmaps project

Reused:
- **File-based human-readable artifacts** — but as a **render-on-demand export** of DB rows, not a source of truth.
- **State-as-events pattern** — now `node_state_event` rows instead of `State/*.md` files.
- **Deterministic next-step selection** — now a SQL query over `node_dependency` + `node_state_event` instead of regex over markdown.
- **YAML-frontmatter-style metadata** — now first-class columns on `plan_node`.

Dropped:
- **Flat step list** — replaced by tree + DAG.
- **Positional step numbers** — replaced by stable IDs + fractional position + display-time outline numbering.
- **No-parallelism rule** — replaced by dependency-aware parallel dispatch.
- **Markdown backend as primary store** — replaced by SQLite.
- **Flask dashboard as the observability path** — replaced by the arbitrator's `event` stream (any UI can tail it).

## Conformance with project rules

Spot-checked against `.claude/rules/db-schema-design.md`:

- **No blobs** in primary rows — bodies isolated in the `body` side-table.
- **No computed values** — counts, completion percentages, latest-state-per-node all derive from queries.
- **No unstructured lists** — dependencies, gate options, session properties, node state transitions each get their own table.
- **Indexable columns only** — every primary-table column is a typed scalar suitable for `WHERE` / `JOIN` / `ORDER BY`.
- **Meaningful names** — `creation_date` not `created_at`; `plan_node` not `parent_id_node`; project vocabulary (specialist, speciality, team-lead).
- **Flexible type columns** — `node_kind`, `event_kind`, `message_type`, `artifact_kind`, `attempt_kind` avoid predicted columns.
- **Separate tables when warranted** — state events are written later by different actors (→ own table); dependencies are many-per-node (→ own table); gate options are many-per-gate (→ own table).

Also:
- **Structured markdown for team definitions, never Python** (per memory) — playbook authoring per the conductor doc uses Python but *declarations*, not programs. Playbook choice is orthogonal to this schema and already decided there.

## Open items (deferred)

- **Markdown export format.** The roadmap needs a read-only markdown rendering for humans / git / review. Directory layout and front-matter structure to be specified in a follow-up plan.
- **Session scope options.** Schema supports "one session per run" (default), "one session per primitive," and batching. Decision deferred until the executor team-lead's behavior is being authored.
- **Cycle-detection policy.** Insertions into `node_dependency` can in principle create cycles. Recommend write-time detection (walk ancestors on insert) but the detail is deferred.
- **Retention policy.** `event` is a firehose; long-running projects will accumulate many rows. Pruning / archival policy (per-session or per-time) to be decided operationally.
- **Schema validation surface.** `schema_valid` on `dispatch` records pass/fail but not the validation error detail. May need a sibling `dispatch_error` table if we want queryable error codes.

## Followups

- **Implementation plan** — `docs/planning/2026-04-17-atp-roadmap-plan.md` — lists the schema migration file, arbitrator resource stubs, and removals (markdown-backend resources that collide, `scripts/project_storage.py` absorption, architecture.md update).
- **Arbitrator contract tests** — per-resource contract tests in `tests/arbitrator/` covering the new resources.
- **architecture.md update** — once this design plus the conductor plan both ship, rewrite `docs/architecture.md` to describe the integrated system. Per the conductor doc's convention, `architecture.md` is current-state, not aspirational.
