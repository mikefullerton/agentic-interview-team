# Dev-Team Planning Todo

_Last refreshed 2026-04-18 — see `docs/architecture.md` for current state._

## In Progress

- _(nothing actively in flight)_

## Todo

### Roadmap follow-ups (post-PRs #10-15, #23)

- **Markdown export format spec.** Directory layout + front-matter for the read-only human-rendering of a roadmap. Design doc § "Open items".
- **Cycle-detection policy.** `node_dependency` inserts can create cycles. Recommend write-time ancestor walk; pin the detail.
- **Session scope options.** Schema supports one-session-per-run, one-per-primitive, and batching. Decide once executor team-lead behavior is being authored.
- **Event-table retention.** Long-running projects will balloon `event`. Pick a pruning / archival policy.
- **Dispatch / attempt tables on the live conductor schema.** Reference schema-v3.sql has them; live schema doesn't yet. When they land:
  - extend `testing/unit/tests/conductor/contract/test_cross_stream_filter.py` to 11 streams
  - add round-trip tests for `dispatch` + `attempt`
  - update `plugins/dev-team/scripts/db/schema_lint.py` exemption list

### atp planning surface

- **`atp plan <team>` command.** Drives the planner specialty against a team to produce a roadmap. Was the next item before the contract-tests pivot — needs a fresh plan doc.

### Team roles

- **Persona support for team-lead and specialists.** Give each role a persona surface (voice, perspective, priors) so prompts aren't anonymous. Decide where it lives — team.md front-matter vs. per-role file — and how it feeds into specialist invocations.

### Integration surface

- **Plugin scheme for interacting with the team.** Transport-neutral Session API + event stream so any host (native Mac chat app, CLI, Slack, web) can drive a team. Design: [`2026-04-18-integration-surface-design.md`](./2026-04-18-integration-surface-design.md). Plan: [`2026-04-18-integration-surface-plan.md`](./2026-04-18-integration-surface-plan.md) — 6 tasks in order.
- **`atp rollcall` command.** Pings every team-lead / specialist / specialty worker / specialty verifier through the integration surface and reports identity + reachability. Design + plan: [`2026-04-18-rollcall-design.md`](./2026-04-18-rollcall-design.md). Depends on integration surface Task 1.

### Tooling

- **Session-start submodule staleness advisory.** Stop hook no longer enforces submodule freshness (per fix `cat-herding/main` `fae0faa`). Replace with informational surfacing at session start (e.g. via `cc-repo-state` or a session-start hook) so drift is visible without forcing random bumps.
- **cc-* test harness.** Brainstormed shape: pytest in cat-herding repo, temp git repos as fixtures, fake `gh` for PR-touching scripts. Scope and gh strategy still open.

### Documentation

- **`docs/architecture.md` update.** Once the conductor + roadmap designs are both fully landed, rewrite to current-state per the doc's own convention.

## Recently Done

- **Contract tests for roadmap arbitrator resources** (PR #23, 2026-04-18) — 28 tests under `testing/unit/tests/conductor/contract/`; covers verification items 2-4 (schema lint, tree+DAG round-trip, cross-stream filter).
- **name-a-puppy + legacy runtime retirement** (PR #22).
- **atp follow-ups: full action set, team loader, atp CLI, deprecation** (PR #20).
- **name-a-puppy as roadmap + realizer** (PR #19, #21).
- **Conductor "what's next" specialty + run_roadmap mode** (PR #18, design #17).
- **Roadmap graph + plan_node_id join key + body side-table** (PRs #11, #12, #13, #14, #15).
- **atp roadmap design doc** (PR #10) — `docs/planning/2026-04-17-atp-roadmap-design.md`.
- **Stop-hook fix: drop submodule freshness check** (cat-herding `fae0faa`, 2026-04-18).
