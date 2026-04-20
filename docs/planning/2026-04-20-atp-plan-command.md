# `atp plan <team>` — Design + Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `atp plan <team> [--goal TEXT]` — one conductor session in which a team-lead named `planner` drives the team's specialists in planning mode to emit a roadmap (plan_node rows + node_dependency edges). Output: a `roadmap_id` the caller can later pass to `atp run`/`atp execute`.

**Architecture:** `atp plan` mirrors `atp run` — same CLI entry point, same conductor plumbing, different realizer. A new `plan_realizer` dispatches one `claude -p` call per (specialist, speciality) pair asking each speciality to emit plan_node rows for its own scope; the conductor writes them to the arbitrator. No new schema. Single conductor session per invocation.

**Tech stack:** Reuses conductor + `SpecialistDispatcher` + arbitrator shipped in PRs #27, #28, #32. No new dependencies.

**Context:**
- High-level flow: `docs/planning/2026-04-17-atp-roadmap-design.md` § "Phase 1 — planning"
- Roadmap schema: `plugins/dev-team/services/conductor/arbitrator/backends/schema.sql`
- Existing CLI pattern: `skills/atp/scripts/atp_cli.py::cmd_run`
- Planner role precedent: `testing/fixtures/teams/rollcall_team/team-leads/planner.md`

---

## Scope

**In scope (v1):**
- `atp plan <team> [--goal TEXT] [--dispatcher mock|claude-code] [--db PATH]`
- Team must have `team-leads/planner.md`; otherwise clear error.
- Planner realizer: one dispatch per speciality; each returns a JSON array of `{title, node_kind, specialist, speciality, depends_on}` entries for its scope.
- Conductor writes plan_nodes + node_dependency edges to the arbitrator; commits `roadmap_id` to stdout.
- Mock dispatcher path so unit tests run without the `claude` CLI.

**Out of scope (follow-ups):**
- Lazy HTN re-decomposition of compound nodes (design doc § 41).
- `planning.decompose-node` cross-team request kind (design doc § 539).
- Interactive interview team-lead (`planner` in v1 is a non-interactive JSON emitter).
- Markdown export of the roadmap — already its own todo item.
- Re-planning / patching an existing roadmap.
- Validating that specialist.speciality pairs actually exist in the team — defer to `atp execute` surfacing the error.

---

## Decisions

1. **Planner is a team-lead, not a specialty.** Lives at `teams/<team>/team-leads/planner.md`. One per team. Identity + voice per the rollcall persona convention.
2. **Planner output is flat.** v1 emits only `primitive` nodes. Compound nodes require lazy decomposition plumbing we don't want in v1. Every emitted node has exactly one parent edge (the root compound representing the whole goal).
3. **One dispatch per speciality.** Planner worker is `claude -p` with the speciality's `planner` focus block (new frontmatter field on speciality markdown, falling back to `worker_focus` if absent). Verifier skipped for v1 — roadmap structure gets validated by the arbitrator's existing FK + schema-lint constraints, not a verifier pass.
4. **Session scope: one session per `atp plan`.** Conductor writes directly to the session's `roadmap_id`; session terminates `completed` on success, `failed` on any planner dispatch error.
5. **`atp plan` stdout:** the `roadmap_id` on success (one line, machine-parseable). Human-readable progress on stderr via the integration surface.

---

## File Structure

- Create: `plugins/dev-team/services/conductor/plan_realizer.py` — `make_plan_realizer(manifest, goal)` returning a `realize(arb, dispatcher, session_id, node_id)` async callable.
- Create: `teams/devteam/team-leads/planner.md` — devteam's planner role.
- Create: `testing/fixtures/teams/plan_fixture/` — minimal two-specialty team with a planner for tests.
- Modify: `skills/atp/scripts/atp_cli.py` — add `cmd_plan`, `plan` subparser.
- Modify: `plugins/dev-team/services/conductor/team_loader.py` — optional `planner_focus` field on `SpecialtyDef`.
- Create: `testing/unit/tests/conductor/test_plan_realizer.py`
- Create: `testing/unit/tests/atp/test_cli_plan.py`

---

## Task 1: Planner markdown + team_loader field

**Files:**
- Create: `testing/fixtures/teams/plan_fixture/team.md`, `team-leads/planner.md`, two `specialists/<name>/specialities/<name>.md` files.
- Modify: `plugins/dev-team/services/conductor/team_loader.py`
- Create: `testing/unit/tests/conductor/test_team_loader_planner_focus.py`

- [ ] **Step 1: Write the failing loader test.** Assert `load_team(fixture).specialists["<sp>"].specialties["<sty>"].planner_focus == "<expected>"` when the speciality markdown has a `## Planner Focus` section, and falls back to `worker_focus` when absent.
- [ ] **Step 2: Run it — expect AttributeError.**
- [ ] **Step 3: Add `planner_focus: str` to `SpecialtyDef`. Extend the markdown parser to populate it (`## Planner Focus` heading; fall back to `worker_focus`).**
- [ ] **Step 4: Run — passes.**
- [ ] **Step 5: Commit.**

## Task 2: `plan_realizer` — one dispatch per speciality

**Files:**
- Create: `plugins/dev-team/services/conductor/plan_realizer.py`
- Create: `testing/unit/tests/conductor/test_plan_realizer.py`

- [ ] **Step 1: Write the failing test.** Build a fixture manifest with two specialities; mock dispatcher returns `{"plan_nodes": [{"title": "A", "node_kind": "primitive", "specialist": "...", "speciality": "..."}], "depends_on": []}` per speciality. Call `make_plan_realizer(manifest, goal="build X")` and assert plan_node rows + node_dependency edges land in the arbitrator, scoped to the session's roadmap.
- [ ] **Step 2: Run — module not found.**
- [ ] **Step 3: Implement `make_plan_realizer` mirroring `make_generic_realizer`'s shape. For each (specialist, speciality) in the manifest: dispatch via `SpecialistDispatcher` with `planner_focus` as the worker focus; parse `plan_nodes` from the response; call `arb.create_plan_node` for each and `arb.add_dependency` for each edge.**
- [ ] **Step 4: Run — passes.**
- [ ] **Step 5: Commit.**

## Task 3: `atp plan` CLI subcommand

**Files:**
- Modify: `skills/atp/scripts/atp_cli.py`
- Create: `testing/unit/tests/atp/test_cli_plan.py`

- [ ] **Step 1: Write the failing CLI test.** Invoke `atp plan <fixture-team> --goal "build X" --dispatcher mock --db <tmp>.sqlite`; assert exit 0 and stdout is a single line matching `^rm_[a-z0-9]+$`. Assert `arb.list_plan_nodes(roadmap_id)` returns the mocked rows.
- [ ] **Step 2: Run — subcommand not found.**
- [ ] **Step 3: Add `cmd_plan` to `atp_cli.py`. Args: `team`, `--goal`, `--dispatcher`, `--db`. Load manifest; require `team-leads/planner.md`; build a `_make_conductor_runner` variant wired to `make_plan_realizer`; drive via `InProcessSession`; print `roadmap_id` on stdout.**
- [ ] **Step 4: Run — passes.**
- [ ] **Step 5: Commit.**

## Task 4: devteam planner + end-to-end mock smoke

**Files:**
- Create: `teams/devteam/team-leads/planner.md`
- Create: `testing/functional/tests/test_atp_plan_mock.py`

- [ ] **Step 1: Write the failing smoke test.** Spawns `atp plan devteam --goal "tiny calculator" --dispatcher mock --db <tmp>` as a subprocess; asserts exit 0, a roadmap_id line on stdout, and that the arbitrator contains ≥1 plan_node.
- [ ] **Step 2: Run — fails (no planner.md).**
- [ ] **Step 3: Author `teams/devteam/team-leads/planner.md` with role / persona / phases sections (mirror `analysis.md`'s structure).**
- [ ] **Step 4: Run — passes.**
- [ ] **Step 5: Commit.**

## Task 5: Docs

**Files:**
- Modify: `skills/atp/SKILL.md` (or wherever `atp run` is documented)
- Modify: `docs/planning/todo.md` — strike `atp plan` item, add entry to Recently Done

- [ ] **Step 1: Add a short `atp plan` section mirroring the existing `atp run` block.**
- [ ] **Step 2: Refresh todo.md.**
- [ ] **Step 3: Commit.**

---

## Self-Review Checklist (before PR)

- [ ] `pytest testing/unit/tests/conductor/ testing/unit/tests/atp/` green
- [ ] `pytest testing/functional/tests/test_atp_plan_mock.py` green
- [ ] `atp plan devteam --goal "calculator" --dispatcher mock` emits a roadmap_id, exits 0
- [ ] `atp describe devteam` shows the new planner team-lead
- [ ] No schema changes — arbitrator + schema-lint untouched
