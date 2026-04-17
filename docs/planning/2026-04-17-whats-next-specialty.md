# 2026-04-17 — Conductor "what's next" Specialty

> **Status:** Design spec. Replaces per-team `TeamPlaybook` state machines with a conductor-owned specialty pair that decides the next action by reading the roadmap graph.
>
> **Depends on:** [`2026-04-17-atp-roadmap-design.md`](./2026-04-17-atp-roadmap-design.md) — the graph schema this specialty queries.
>
> **Supersedes:** per-team playbook authoring as the primary orchestration mechanism. `name_a_puppy*.py` remain prototype-only scaffolding.

## Purpose

One specialty, owned by the conductor, that drives every session. Instead of a hand-written state machine per team, the conductor loops:

```
while session has incomplete work:
    decision = dispatch("whats-next")
    if decision.deterministic: advance
    else: verified_decision = dispatch("whats-next-verifier", decision) ; advance
```

The worker reads durable state and returns the next action. The verifier reviews the worker's reasoning against a checklist. Crash recovery is the same loop — a resumed session re-invokes the worker and gets a fresh decision.

## Ownership

**Conductor-owned.** Not a team specialty, not in any team's manifest.

- Registered on `Conductor` at construction.
- Dispatched through the same `Dispatcher` / `specialist_runner` path as team specialties.
- Agent names: `whats-next-worker`, `whats-next-verifier`.
- `agent_kind` per dispatch row: `speciality-worker` / `speciality-verifier` (existing enum values).

Teams no longer declare `TeamPlaybook` state machines. A team.md declares a manifest; a roadmap of `plan_node`s expresses *what* the team does. The conductor runs it.

## Worker input (what it reads)

Queried via the arbitrator before dispatch and packed into the worker's prompt context:

| Source | Fields |
|---|---|
| `session` | `session_id`, `playbook`, `roadmap_id`, `plan_node_id` (anchor), `status` |
| `plan_node` (whole roadmap) | `node_id`, `parent_id`, `position`, `node_kind`, `title`, `specialist`, `speciality`, body |
| `node_dependency` | all edges for the session's roadmap |
| `node_state_event` (latest per node) | `event_type`, `actor`, `event_date` |
| `state` (active) | unfinished call-stack — crash-resume signal |
| `gate` | open gates (`status = open`) |
| `request` | in-flight requests (`status ∈ {pending, queued, in-flight}`) |
| `finding` (since anchor) | recent findings that may trigger re-decomposition |

This is exactly the set of tables listed as per-session + project streams in the roadmap design doc. No new tables.

## Worker output

```json
{
  "action": "advance-to | decompose | await-gate | re-decompose | await-request | present-results | done",
  "node_id": "<plan_node_id or null>",
  "reason": "<one sentence>",
  "deterministic": true | false
}
```

Legal `action` values:

| Action | Meaning | Triggers |
|---|---|---|
| `advance-to` | Start realizing a ready primitive. | All deps `done`, no open gates on it. |
| `decompose` | Expand a compound node via specialist planning-mode. | Compound node is `ready` with no children yet. |
| `await-gate` | Block until an open gate is answered. | A ready node has an open gate. |
| `re-decompose` | Ask a compound to expand given new findings. | A node has recent findings that may warrant new children. |
| `await-request` | Block until an in-flight request completes. | The next candidate node depends on a pending `request`. |
| `present-results` | All primitives done; hand back to user. | No remaining work. |
| `done` | Terminate session. | User accepted results (or no session-level gate is open). |

Response schema (strict, enforced by the arbitrator):

```json
{
  "type": "object",
  "properties": {
    "action":        {"type": "string", "enum": ["advance-to","decompose","await-gate","re-decompose","await-request","present-results","done"]},
    "node_id":       {"type": ["string","null"]},
    "reason":        {"type": "string", "minLength": 1, "maxLength": 280},
    "deterministic": {"type": "boolean"}
  },
  "required": ["action","reason","deterministic"]
}
```

## Verifier checklist

Invoked **only when the worker returns `deterministic: false`**. The verifier runs the same input plus the worker's proposed action and must confirm:

1. **Node exists and has the claimed state.** Worker's `node_id` appears in the roadmap with the required `node_state_event` history.
2. **Dependencies satisfied.** For `advance-to`: every `depends_on` row for this node has a latest `node_state_event` of `done`.
3. **No open gates ignored.** No `gate` row with `status = open` targets this node.
4. **No in-flight request ignored.** No `request` row with `status ∈ {pending, queued, in-flight}` targets this node.
5. **No higher-priority branch.** Worker didn't pick a lower-priority node when a different ready node exists that the verifier considers clearly preferred; verifier may say "retry with alternatives".
6. **Crash state handled.** If `state` has unfinished rows, the action must either `advance-to` the resume anchor or explicitly `await-*`. Verifier rejects actions that leave dangling state.

Verifier response:

```json
{
  "verdict": "pass | fail | verified | retry-with",
  "alternative_action": null | <same shape as worker output>,
  "reason": "<one sentence>"
}
```

`pass` / `verified` — accept worker decision. `retry-with` — verifier proposes a specific alternative. `fail` — escalate (open a `gate` for user).

## Deterministic short-circuit rules

The worker is **not dispatched** when all of the following hold. The conductor computes the answer in Python and records a synthetic dispatch row for audit.

- Exactly one node is `ready` (all deps done, no open gate, no pending request).
- The session has zero unfinished `state` rows (no crash recovery pending).
- No new findings since the anchor (no `finding` rows with `creation_date > session.last_decision_date`).
- No open session-level gates.

Under these conditions the conductor emits `action: advance-to, deterministic: true` without an LLM call. The verifier is skipped. This keeps linear DAGs cheap.

When any condition fails — branch point, crash, gate, new finding — the full worker+verifier dance runs.

## Crash recovery integration

No special resume code path. On conductor start with an existing `session_id`:

1. Load session row → `status`, `last_task_id`, `last_state_id`, `last_event_sequence`.
2. Run the main loop. The first iteration's `whats-next-worker` sees active `state` rows and returns either a resume action (`advance-to` the interrupted node) or `await-*` (a request/gate was in flight).
3. Worker is deterministic for the trivial case (exactly one active state, no ambiguity).

The "session was in an error state" case is the normal case for this specialty — it's built for partial state.

## Interaction with team manifests

Teams still declare specialists and specialties in their manifests. These execute the nodes the worker chooses.

```
conductor.whats-next-worker       ←  owned by conductor
conductor.whats-next-verifier     ←  owned by conductor

team.<specialist>.<specialty>     ←  owned by the team, dispatched when
                                     worker returns advance-to a primitive
team.<specialist>.planning-mode   ←  owned by the team, dispatched when
                                     worker returns decompose
```

The conductor has the one and only orchestration brain; teams have domain workers.

## What gets retired

- `TeamPlaybook.states`, `transitions`, `judgment_specs`, `initial_state` — all become vestigial.
- `JudgmentSpec`, `State`, `Transition`, `JudgmentCall`, `DispatchSpecialist`-as-action — the action types used by the state machine.
- `name_a_puppy.py`, `name_a_puppy_v2.py`, `pet_coach.py`, `project_management.py` — kept as reference only; not loaded by the runtime.
- `TeamLead` (the current state-machine stepper) — replaced by a conductor loop that dispatches the `whats-next` pair.

`TeamPlaybook.manifest` and `TeamPlaybook.request_handlers` survive — still needed for specialist/specialty declaration and inter-team RPC.

## Prompts (draft — to be refined)

### `whats-next-worker`

> You are the scheduler for an agentic session. Below is the current roadmap, the state-event log, active in-flight work, open gates, and recent findings. Return the single next action. If the situation is unambiguous (one ready node, no gates, no crash state), return `deterministic: true`. Otherwise return `deterministic: false` and explain briefly.
>
> Roadmap: {roadmap_json}
> State events: {state_events_json}
> Active state: {active_state_json}
> Open gates: {open_gates_json}
> In-flight requests: {in_flight_requests_json}
> Recent findings: {findings_json}
>
> Return JSON matching the schema in the spec.

### `whats-next-verifier`

> The scheduler proposed: {worker_output_json}
> Here is the same input it saw: {context_json}
>
> Check the checklist in §"Verifier checklist". Return `pass` if the decision is sound, `retry-with` + an alternative if another node is clearly better, or `fail` if you need user input.

Model tier: `balanced` for both. `fast-cheap` may be viable later if the prompts stabilize.

## Validation / prototype path

1. **Unit-shape test** — give the worker a fabricated roadmap + state and assert the deterministic short-circuit fires for a pure linear DAG with no ambiguity. No LLM in this test.
2. **Mock-dispatcher e2e** — 3-node linear plan (`gather → dispatch → present`) driven by the loop against `MockDispatcher`. Replaces `name_a_puppy_v2` as the first real validation.
3. **DAG-parallelism e2e** — 3-node diamond (`A → {B, C} → D`). Confirm two nodes run in parallel via the conductor's existing `asyncio.gather`.
4. **Crash-resume e2e** — kill mid-dispatch; restart; confirm the worker's first call returns `advance-to` the interrupted node.
5. **Branch-point e2e** — two ready nodes; confirm worker+verifier dispatched, decision made, dispatch rows recorded.

(1)–(5) together prove the new model end-to-end. Only after that does the atp-plan / atp-execute playbook work move forward.

## Open items

- **Prompt context size.** Big roadmaps could blow out context. Mitigations: summarize completed subtrees, include only nodes within N hops of active work. Defer until a real roadmap exceeds budget.
- **Verifier loop bound.** If `retry-with` cycles, cap at 2 retries then open a `gate` for user.
- **"No new findings" detection.** Needs a `session.last_decision_date` field or equivalent. Minor schema addition; add with the first implementation PR.
- **Deterministic path's dispatch row.** Audit wants a record per decision. Insert a synthetic `dispatch` row with `concrete_model = "deterministic"` and `schema_valid = 1`. Keeps the audit log uniform.

## Followups

- **Implementation plan** — `docs/planning/2026-04-17-whats-next-specialty-plan.md`, listing the conductor refactor, the new dispatch helpers, and the test files above.
- **Architecture update** — once this specialty ships, rewrite `docs/architecture.md`'s orchestration section to describe the loop instead of playbook state machines.
- **Playbook retirement** — mark `TeamPlaybook.states/transitions/judgment_specs` as deprecated in code comments; plan a follow-up PR that removes them once no code references them.
