# 2026-04-18 — Roll-Call Command Design

> **Status:** Design + plan. One-shot — small enough not to warrant a separate plan doc.
>
> **Depends on:** [`2026-04-18-integration-surface-design.md`](./2026-04-18-integration-surface-design.md) and [`2026-04-18-integration-surface-plan.md`](./2026-04-18-integration-surface-plan.md) — roll-call is a **host** against the integration surface. Shipped after integration surface Task 1 (in-process transport + `fake_team` + contract suite).

## Purpose

Give the user a single command to ping every role in every team and confirm each one is reachable and responsive. Roll-call is both a **diagnostic** ("are all my roles alive?") and a **demo** of the integration surface ("every role really does go through the same pipeline"). No side door — roll-call opens a real session per role and sends a real user turn.

## The roll-call prompt

Fixed, standardized, one change point.

```
You are participating in a roll-call. In one sentence, state:
(a) your role, (b) the team you serve, (c) any readiness concerns.
```

Sent as a plain `user` turn via `Session.send(...)`. The role's response arrives as `text` events terminated by `result`. Identical shape to what the Mac chat app or Slack host would see.

## Scope

- **In scope (v1):** role identity + reachability. Proves the LLM call path, the prompt routing, and the integration surface wiring.
- **Out of scope (v1):** tool / MCP health. A specialist whose tools are unreachable will still happily introduce itself. Filed as a follow-up "deep roll-call" that invokes a trivial tool per role.

## Role discovery

`plugins/dev-team/services/rollcall/discovery.py` walks the `teams/` tree and returns a flat list:

```python
@dataclass(frozen=True)
class RoleRef:
    team: str
    kind: Literal["team-lead", "specialist", "specialty-worker", "specialty-verifier"]
    name: str
    path: Path
```

Sources:
- **team-lead** → `teams/<team>/team-leads/<lead>/`
- **specialist** → `teams/<team>/specialists/<specialist>/`
- **specialty-worker / specialty-verifier** → per-specialist specialty manifest (worker + verifier pair)

Reuses existing `team_loader.py` primitives — no new parsing.

## Orchestrator

`plugins/dev-team/services/rollcall/orchestrator.py` is a host against the integration surface. For each `RoleRef`:

```
start(team, prompt=role_scoped_preamble, options=role_options)
  → SessionHandle
send(session_id, roll_call_prompt)
  → consume events until `result`
  → assemble RollCallResult(role=ref, response=joined_text, duration=t, error=None)
close(session_id)
```

Sessions run concurrently up to a bounded `asyncio.Semaphore` (default 4) to avoid hammering the model. Errors from any role become a `RollCallResult.error` rather than aborting the whole run.

### Result shape

```python
@dataclass(frozen=True)
class RollCallResult:
    role: RoleRef
    response: str          # joined text events
    duration_ms: int
    error: RollCallError | None
```

## CLI

`/atp rollcall [<team>] [--format table|json] [--concurrency N]`

- No argument → iterate every declared team.
- `<team>` → scope to one team.
- `--format table` (default) → streams per-role status lines as they arrive, prints a summary table on finish.
- `--format json` → emits one `RollCallResult` per line (NDJSON) as they complete.
- Exit 0 iff every role returned a `result` with no `error`; else exit 2 with the count of failures.

Sample output (`table`, trimmed):

```
TEAM          ROLE                           STATUS   TIME   NOTE
devteam       team-lead/orchestrator         ok       2.1s
devteam       specialist/architect           ok       1.8s
devteam       specialty-worker/architect.code ok      2.4s
devteam       specialty-verifier/architect.code failed 12.0s  timeout
…
```

## Tests

### Contract test (unit)

`testing/unit/tests/conductor/rollcall/test_rollcall.py`.

Fixture team under `testing/fixtures/teams/rollcall_team/`:
- 2 team-leads
- 3 specialists × (worker + verifier) = 6 specialty roles
- **Total: 8 roles**

Runs against the integration surface in-process transport + `FakeTeam`. `FakeTeam` is configured to emit a scripted 3-event sequence per role: `state: starting` → `text(introduction)` → `result`.

Asserts:
- Discovery found all 8 roles.
- Orchestrator opened exactly 8 sessions (one per role), all closed cleanly.
- Every `RollCallResult.response` is non-empty.
- Emitted event stream passes the integration surface schema linter.
- CLI `--format json` output has 8 lines, each a valid `RollCallResult`.
- Golden-file diff on the `table` output (rendered against the fixture team).

### Functional smoke (real LLM)

`testing/functional/tests/rollcall/test_rollcall_real.py`. Gated by `AGENTIC_REAL_LLM_SMOKE=1`. Runs against `teams/puppynamingteam/` (small, known team). Asserts every role returned non-empty text within a generous timeout. No response-content assertions — the real LLM isn't required to say anything specific.

## File layout

### New

```
plugins/dev-team/services/rollcall/
  __init__.py
  discovery.py
  orchestrator.py
  formatting.py              # table + json renderers

plugins/dev-team/skills/atp/scripts/atp_cli.py
  # add `rollcall` subcommand

testing/fixtures/teams/rollcall_team/
  team.md
  index.md
  team-leads/…
  specialists/…

testing/unit/tests/conductor/rollcall/
  __init__.py
  conftest.py
  test_rollcall.py

testing/functional/tests/rollcall/
  __init__.py
  test_rollcall_real.py
```

### Modified

```
plugins/dev-team/skills/atp/SKILL.md   # document the subcommand
docs/planning/todo.md                  # link to this doc
```

## Plan

One PR. Tasks execute in order; each ends green.

### Task 1 — Discovery

- [ ] Implement `discovery.py` using `team_loader` primitives. Return `List[RoleRef]`.
- [ ] Unit test: load the fixture team, assert the 8 expected `RoleRef` values.
- [ ] Commit: `feat(rollcall): role discovery`.

### Task 2 — Orchestrator

- [ ] Implement `orchestrator.py` against `TeamSession`. Bounded concurrency via `asyncio.Semaphore`. Per-role error capture.
- [ ] Wire `FakeTeam` scripts for roll-call shape (starting → text → result).
- [ ] Unit test: orchestrator over the fixture team produces 8 `RollCallResult` values; all `error=None`; every `response` non-empty.
- [ ] Commit: `feat(rollcall): orchestrator`.

### Task 3 — CLI + formatting

- [ ] Implement `formatting.py` (table + json).
- [ ] Add `rollcall` subcommand to `atp_cli.py`.
- [ ] Unit test: `--format json` produces one line per role; `--format table` matches golden file.
- [ ] Commit: `feat(rollcall): atp rollcall CLI`.

### Task 4 — Schema conformance + CLI exit code

- [ ] Run the integration surface schema linter over every emitted event in the test; assert clean.
- [ ] Unit test: one role fails → exit code 2, summary names the failed role.
- [ ] Commit: `test(rollcall): schema + failure-path`.

### Task 5 — Functional smoke

- [ ] `test_rollcall_real.py` gated by `AGENTIC_REAL_LLM_SMOKE=1`.
- [ ] Commit: `test(rollcall): real-LLM smoke`.

### Task 6 — Docs

- [ ] Short section in `plugins/dev-team/skills/atp/SKILL.md`.
- [ ] Update `docs/planning/todo.md`.
- [ ] Commit: `docs(rollcall): document rollcall subcommand`.

## Verification

1. **Discovery finds every role.** Fixture team: 8 roles, all `RoleRef` kinds represented.
2. **One session per role.** Orchestrator opens and closes exactly N sessions; no leaks.
3. **Pipeline fidelity.** Every emitted event passes the integration surface schema linter.
4. **Failure isolation.** One role failing does not abort the run; CLI exit code is 2.
5. **Real-LLM smoke.** `puppynamingteam` roll-call completes with non-empty responses.

## Open items

- **Concurrency default.** 4 is a guess. Revisit once real-LLM smoke tells us what the model rate limits do.
- **Deep roll-call.** v1 is identity-only. If tool/MCP health becomes a real diagnostic need, add a second prompt that asks the role to invoke a trivial tool.
- **Output persistence.** Should roll-call results land in an `event` row (or its own table) so a human can review past runs? Not obviously needed; keep stdout-only until a use case appears.
