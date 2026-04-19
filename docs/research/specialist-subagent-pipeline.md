# Specialist Subagent Pipeline — Research Notes

> Captured during the 2026-04-19 design session. Informs an upcoming
> refactor of the conductor's execution pipeline.

## Current Pipeline (as of 2026-04-19)

- **Unit of execution:** one plan_node → one `claude -p` subprocess.
- **Implementation:** `plugins/dev-team/services/conductor/generic_realizer.py`.
- **Dispatch shape:** the realizer builds an `AgentDefinition` for a worker,
  calls `ClaudeCodeDispatcher.dispatch(...)`, which shells out to `claude -p`
  with `--agents '{<worker-name>: {...}}'` and `--output-format stream-json`.
- **No verifier in the loop.** `generic_realizer.py:21` explicitly notes
  *"Verifier is not called here; that's a follow-up."*
- **Data model:** `dispatch` rows per `claude -p` call; `attempt` rows
  group worker + verifier dispatches with a verdict (see
  `plugins/dev-team/scripts/db/schema-v3.sql` — `dispatch` and `attempt`
  tables). These exist in the reference schema; the live conductor schema
  has not yet adopted them.

## Proposed Pipeline

**Specialist becomes a `claude -p` subprocess; worker and verifier become
subagents the specialist dispatches via the Task tool.**

```
conductor                              specialist subprocess
─────────                              ──────────────────────
for plan_node N:                       (claude -p, system prompt = specialist)
  open dispatch #S                     │
  spawn `claude -p` ───────────────────┤ Task speciality-worker (input: worker_focus + upstream)
                                       │   └─ dispatch #W (parent=S)
                                       │ Task speciality-verifier (input: worker output + verify criteria)
                                       │   └─ dispatch #V (parent=S)
                                       │ (if fail, retry worker+verifier inside the subprocess)
                                       │ emit final result: {attempts: [...]}
  close dispatch #S                    │
  write attempt rows from final result │
```

## Motivation

- **Isolation** — subagents get fresh context windows, parent's context stays
  uncluttered.
- **Parallelism** — the Task tool supports concurrent subagent calls, so a
  specialist can run several specialities (or speculative attempts) in parallel.
- **Speed** — the specialist subprocess pays the project-context setup cost
  (CLAUDE.md, graphify, memory) **once** per plan_node, not three times
  (worker, verifier, judgment).

## Subagent Definitions — One Per Kind, Not Per Specialty

Initial thought: define a subagent per `(specialist, speciality, role)` — e.g.
`platform-database.indexing.worker`, `platform-database.indexing.verifier`, …
That balloons to `2 × N_specialities` definitions and requires every
specialist's `--agents` payload to re-serialize the full set.

**Better:** two global, topic-agnostic subagents — the "brain + hands"
decoupling pattern from Anthropic's *Managed Agents* (Engineering blog,
[link](https://www.anthropic.com/engineering/managed-agents)):

- `speciality-worker` — "Given a focus prompt and upstream context, do the
  work. Return structured output."
- `speciality-verifier` — "Given worker output and verify criteria, return
  a verdict."

The topic (worker_focus, verify criteria) is **passed as input** to the
Task call, not baked into the subagent definition. This matches the article's
`execute(name, input) → string` shape — subagents are stateless hands; the
specialist is the brain that holds topic knowledge and sequences work.

**`team.json` is the content library.** The specialist reads its own
`team.json` entry at runtime (it's already pre-loaded into the subprocess
via the specialist's system prompt or a read-only tool) and passes the
right `worker_focus` / `verify` text into each Task call.

Consequences:
- Adding a new speciality requires **zero subagent definition changes** —
  just a new row in `team.json`.
- The `--agents` payload is small and fixed: two entries.
- Subagent definitions stay in version control as part of the plugin,
  not hot-loaded from `team.json`.

## Schema Change (Additive)

`dispatch` in `schema-v3.sql` already carries the right fields for
individual calls. One additive change models parent→child dispatches:

```sql
ALTER TABLE dispatch ADD COLUMN parent_dispatch_id TEXT
    REFERENCES dispatch(dispatch_id);
CREATE INDEX idx_dispatch_parent ON dispatch(parent_dispatch_id);
```

Widen `dispatch.agent_kind` vocabulary to include `"specialist"` alongside
`"worker"` / `"verifier"`. `attempt` stays as-is — it already FKs to
`worker_dispatch_id` and `verifier_dispatch_id`.

## Reporting Flow

**Conductor infers child dispatches from stream-json; specialist declares
attempt groupings.**

1. **Child dispatches — inferred.** The conductor already parses stream-json
   events from the specialist subprocess (see `ClaudeCodeDispatcher._drain_stdout`
   at `plugins/dev-team/services/conductor/dispatcher/claude_code.py:122`).
   When a `tool_use` event for `Task` is seen, open a child `dispatch` row
   with `parent_dispatch_id` = specialist's dispatch_id, `agent_kind`
   derived from the Task's subagent name. On `tool_result`: close it.
2. **Attempt groupings — declared.** The specialist's final structured
   result includes `{"attempts": [{worker_dispatch_id, verifier_dispatch_id,
   verdict, ...}]}`. The conductor uses that declaration to write
   `attempt` rows. Trying to infer attempt boundaries from tool_use
   sequence alone is fragile — the specialist knows which worker+verifier
   pair belong together.

## Retry/Judgment Loop Ownership

**Lives in the specialist, not the conductor.** Reasoning:

- The conductor already treats each plan_node as opaque work.
- The retry loop needs the worker's output, upstream context, and specialty
  focus — all of which are already in the specialist's subprocess.
- Round-tripping through SQLite between every worker→verifier→retry step
  is pure overhead; the specialist can hold that state in-process.
- The conductor becomes a *dispatcher of plan_nodes*, not an *orchestrator
  of attempts*. Cleaner separation.

The conductor still owns plan_node-level retries (specialist subprocess
crashes, times out, returns garbage) via its existing scheduler.

## Anthropic "Managed Agents" — Relevant Takeaways

Article: [https://www.anthropic.com/engineering/managed-agents](https://www.anthropic.com/engineering/managed-agents)

Core patterns that map cleanly onto this work:

- **Decouple brain from hands.** Brain = specialist (`claude -p` subprocess
  with project context). Hands = stateless worker/verifier subagents.
- **Stateless tool calls.** Every Task call is fully parameterised by its
  input — no implicit session state on the hand side.
- **Externalise session state.** The arbitrator DB already is this for our
  system. Subagents emit events back to the conductor via stream-json →
  rows in `event`, `dispatch`, `result`, `attempt`.
- **Graceful degradation.** Treat subagent failure as a tool-call error the
  specialist can retry, route elsewhere, or report up.

Pitfalls called out by the article that we should avoid:

- **Monolithic coupling** — don't bundle brain + hands + state into one
  container. Our arbitrator is durable; keep it that way.
- **Stale harness assumptions** — don't encode per-model workarounds in
  the specialist system prompt. `--model` is already configurable per
  dispatch via `DEFAULT_MODEL_MAP` in `claude_code.py:29`.

## Open Questions

- **Specialist pre-registered vs. generic?** Option A: one subagent
  definition per specialist (loaded from `team.json`). Option B: one
  generic `specialist` subagent whose system prompt is passed in at
  runtime, matching the worker/verifier pattern. B is more consistent
  with brain/hands decoupling but makes it harder to ship specialist
  behavior as versioned files on disk.
- **`--agents` payload size.** Two entries (worker + verifier) is small,
  but if we add more kinds of hands (e.g. consultant, reviewer), we need
  to decide whether they're passed per-call or registered once per
  specialist subprocess.
- **Subagent concurrency limits.** Claude Code's Task tool supports
  parallel invocations. Need to measure actual parallelism cap and
  whether our stream-json parser handles interleaved tool_use/tool_result
  events correctly (it currently assumes serial).
- **Propagating plan_node_id.** Child dispatches need `plan_node_id` so
  the existing cross-stream filter (see Task 6 of
  `docs/planning/2026-04-17-atp-roadmap-contract-tests.md`) continues to
  work. Conductor should stamp it on child dispatches from the specialist's
  parent dispatch row.

## References

- `plugins/dev-team/services/conductor/generic_realizer.py` — current
  worker-only execution path.
- `plugins/dev-team/services/conductor/dispatcher/claude_code.py` — stream-json
  parsing and `claude -p` invocation.
- `plugins/dev-team/scripts/db/schema-v3.sql` — `dispatch` and `attempt`
  tables in the reference schema.
- `docs/planning/2026-04-17-atp-roadmap-contract-tests.md` — Scope Notes
  section already flags dispatch/attempt as not-yet-in-live-schema.
- `claude-agents-overview.md` (user's personal reference) — Claude Code
  agent/subagent distinction.
- Anthropic, *Managed Agents*,
  [https://www.anthropic.com/engineering/managed-agents](https://www.anthropic.com/engineering/managed-agents).
