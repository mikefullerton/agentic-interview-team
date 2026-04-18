# Dev-Team Architecture

Single source of truth for the dev-team system. For LLM consumption.

> **Two runtimes coexist.**
>
> 1. **Roadmap runtime (current work)** — `Conductor.run_roadmap` drives a
>    roadmap graph through `WhatsNextSpecialty` + a realizer. Teams are
>    declared as markdown (`teams/<name>/`), loaded into a `TeamManifest`,
>    and executed via the generic realizer. Entry point: the `/atp` skill.
>    No per-team `TeamPlaybook` Python; the conductor's scheduling
>    specialty decides each step. See
>    [`planning/2026-04-17-whats-next-specialty.md`](planning/2026-04-17-whats-next-specialty.md).
>
> 2. **Legacy playbook runtime** — `Conductor.run` still drives hand-authored
>    `TeamPlaybook` state machines (`services/conductor/playbooks/*.py`).
>    Retained for backward compat and as reference examples; new teams should
>    not author one. The `TeamPlaybook.states / transitions / judgment_specs`
>    fields are deprecated and scheduled for removal once the last playbook-
>    driven test/session is migrated.
>
> Both runtimes share the arbitrator, dispatcher, state/gate/request/event
> tables, and the roadmap graph schema
> ([`planning/2026-04-17-atp-roadmap-design.md`](planning/2026-04-17-atp-roadmap-design.md)).
> The conductor architecture paper is
> [`planning/2026-04-11-conductor-architecture.md`](planning/2026-04-11-conductor-architecture.md);
> it remains the reference for inter-team requests, dispatcher semantics,
> and the event stream.

## Roadmap Runtime (current work)

```
/atp run <team>
  │
  ▼
atp_cli.py
  │  load_team(teams/<team>/) → TeamManifest
  │  build_roadmap(arbitrator) from manifest (one node per specialty)
  │  open_session with roadmap_id
  ▼
Conductor.run_roadmap([WhatsNextSpecialty()], realize_primitive=…)
  ├── scheduler loop:
  │     • deterministic short-circuit when unambiguous
  │     • worker → verifier (with bounded retry) when not
  │     • fail-path opens a `conflict` gate and awaits resolution
  ├── advance-to: parallel asyncio.gather over runnable primitives
  ├── decompose / await-gate / await-request / present-results
  │   each call out to pluggable handlers
  └── records node_state_event (running/done) per primitive
```

Files:
- `plugins/dev-team/services/conductor/conductor.py` — `run_roadmap`.
- `plugins/dev-team/services/conductor/specialty/base.py` — `ConductorSpecialty` protocol, `ActionDecision`.
- `plugins/dev-team/services/conductor/specialty/whats_next.py` — the scheduler specialty.
- `plugins/dev-team/services/conductor/team_loader.py` — team.md / specialist.md / specialty.md parser.
- `plugins/dev-team/services/conductor/generic_realizer.py` — manifest-driven realizer.
- `plugins/dev-team/services/conductor/user_interaction.py` — `ask_user` for interview-style realizers.
- `skills/atp/scripts/atp_cli.py` — `/atp` subcommands.

Tests:
- `testing/unit/tests/conductor/test_whats_next_*.py` — scheduler paths.
- `testing/unit/tests/conductor/test_conductor_roadmap_e2e.py` — linear / diamond / smoke.
- `testing/unit/tests/conductor/test_run_roadmap_actions.py` — all 7 action handlers.
- `testing/unit/tests/conductor/test_crash_resume_roadmap.py` — resume.
- `testing/unit/tests/conductor/test_branch_point_gate.py` — verifier-fail gate.
- `testing/unit/tests/conductor/test_team_loader_and_generic_realizer.py` — team markdown → run.
- `testing/unit/tests/conductor/test_name_a_puppy_roadmap.py` + `test_name_a_puppy_interview.py` — puppy roadmap end-to-end.
- `testing/functional/tests/conductor/test_real_llm_puppy_smoke.py` — real-LLM smoke (gated by `AGENTIC_REAL_LLM_SMOKE=1`).

The rest of this doc describes the pre-conductor dev-team skill pipeline, which remains in place for `/dev-team <command>` workflows. Treat it as historical context; new capabilities land in the roadmap runtime.

## System Overview

The dev-team is a Claude Code plugin that provides a multi-agent pipeline for product discovery, analysis, and project building. It is distributed via the agentic-cookbook marketplace.

Three repos:
- **agentic-cookbook** — upstream knowledge: principles, guidelines, compliance checks
- **dev-team** (this repo) — the plugin: agents, specialists, skills, scripts, services
- **Workspace repo** — per-user data: profiles, transcripts, analyses, project builds

Entry point: `/dev-team <command>` — a single skill router that dispatches to workflow files.

## Terminology

| Term | Definition |
|------|-----------|
| **Team-Lead** | Runs a workflow, has a persona, talks to the user. Types: interview, analysis, review, build, audit. |
| **Playbook** | Static definition of a workflow — which team-lead, which specialists, phases, inputs, outputs. (TBD — not yet implemented as a stored type.) |
| **Session** | A playbook being executed — runtime instance with state, tracked by the arbitrator. |
| **Specialist** | Self-enclosed component with a role, persona, cookbook sources, and a manifest of specialty-teams. 22 specialists: 13 domain + 6 platform + 1 project-management + 1 codebase-decomposition + 1 recipe-quality. |
| **Specialty-Team** | Standalone file defining a worker-verifier pair focused on one cookbook artifact. 230 teams across 22 categories in `specialty-teams/`. |
| **Application Map** | Annotated hierarchical decomposition of a codebase produced by the codebase-decomposition specialist. Formal spec at `plugins/dev-team/docs/application-map-spec.md`. Tree structure, file traceability, dependency edges, feature flows, and bottom-up recipe ordering. |
| **Specialty-Worker** | LLM agent. Reads one cookbook artifact, produces structured findings. Isolated — never sees verifier instructions. |
| **Specialty-Verifier** | LLM agent. Checks specialty-worker output for completeness. Returns PASS/FAIL. Isolated — never sees worker instructions. Max 3 retries before escalation. |
| **Consulting-Team** | Standalone file defining a consulting worker-verifier pair focused on one cross-cutting concern. Reviews every specialty-team's output within a specialist. Lives in `consulting-teams/`. |
| **Consulting-Worker** | LLM agent. Reviews a specialty-team's passed output through a cross-cutting lens. Produces VERIFIED or NOT-APPLICABLE. |
| **Consulting-Verifier** | LLM agent. Checks consulting-worker output for completeness. Returns PASS/FAIL. Max 3 retries before escalation. |
| **Observer** | Shell hook + Python script that captures subagent activity via `SubagentStop`. Auto-discovers observer modules in `scripts/observers/`. |
| **Stenographer** | Built-in observer. Writes structured JSONL session log to the session directory. |
| **Specialist-Persona** | LLM agent. Reads raw findings + persona definition, writes persona-voiced interpretations. Translation layer only — produces no new findings. |
| **Result** | One specialist's output for a session. Parent of findings. |
| **Finding** | An individual issue within a result — gap, recommendation, or concern with severity. |
| **Interpretation** | Persona translation of a finding. Written in a later step by the specialist-persona. |
| **Report** | Not a stored type. Query patterns against session data with progressive disclosure (overview → specialist → finding → trace). Designed for LLM consumption. |
| **Dev-team-project** | Project management data — schedules, todos, issues, concerns, dependencies, decisions. NOT a cookbook-project (which is a technical specification for code). One dev-team-project can manage multiple cookbook-projects. |

## Pipeline

How a workflow runs end-to-end:

```
User invokes /dev-team <command>
  → Skill router (SKILL.md) loads config, inits DB, routes to workflow
    → Team-lead runs the workflow, talks to user
      → Team-lead dispatches specialists via arbitrator
        → Specialist script reads assignment
          → Specialty-teams run (worker-verifier loop, max 3 retries)
          → Consulting-teams review (if any — worker-verifier loop per consultant)
          [Observer hook fires on each subagent completion — writes session.log + system log]
          → Specialist-persona writes interpretations
        → Specialist returns result (result_id + pass/fail) via arbitrator
      → Team-lead aggregates results
    → Team-lead presents report to user
```

The team-lead is the only component that talks to the user. All other communication flows through the arbitrator.

## Components

### Skill Router
- **File**: `skills/dev-team/SKILL.md` (v0.6.0)
- Loads config from `~/.agentic-cookbook/dev-team/config.json`
- Initializes shared database via `scripts/db/db_init.py`
- Routes to 8 workflow files based on subcommand

### Team-Leads
5 types: interview, analysis, review, build, audit. Each has a persona and runs a specific category of workflow.

### Specialists
20 specialists in `specialists/`. Each has:
- **Role** — domain scope
- **Persona** — archetype, voice, priorities, anti-patterns
- **Cookbook Sources** — what guidelines/principles they consult
- **Manifest** — list of specialty-team file paths

Domain specialists (13): accessibility, claude-code, code-quality, data-persistence, development-process, devops-observability, localization-i18n, networking-api, reliability, security, software-architecture, testing-qa, ui-ux-design

Platform specialists (6): platform-android, platform-database, platform-ios-apple, platform-web-backend, platform-web-frontend, platform-windows

Project management (1): project-manager

### Specialty-Teams
212 standalone files in `specialty-teams/<category>/<name>.md`. Each has:
- Frontmatter: name, description, artifact, version
- Worker Focus: what the worker analyzes
- Verify: acceptance criteria for the verifier

Parsed by `scripts/run_specialty_teams.py` which reads a specialist's manifest and outputs JSON (name, artifact, worker_focus, verify).

### Agents
20 agent definitions in `agents/`. Key agents:
- `specialty-team-worker.md` / `specialty-team-verifier.md` — the worker-verifier pair
- `transcript-analyzer.md` — interview transcript analysis
- `code-generator.md` — generates code from recipes
- `recipe-writer.md` / `recipe-reviewer.md` — create and review recipes
- `specialist-analyst.md` — analyzes user answers from specialist perspective
- `specialist-code-pass.md` / `specialist-interviewer.md` — (marked for absorption in v2)

### Arbitrator
Abstracted communication conduit between all participants. Single entry point: `python3 scripts/arbitrator.py <resource> <action> [--flags]`.

- Backend-swappable via `ARBITRATOR_BACKEND` env var (default: `markdown`)
- All commands output JSON to stdout, errors to stderr, exit 0/1
- IDs are opaque strings

**Resources**: session, state, message, gate-option, result, finding, interpretation, artifact, reference, retry, report, team-result

**Markdown backend**: stores JSON files in `~/.agentic-cookbook/dev-team/sessions/<session-id>/`. 58 contract tests in `tests/arbitrator/`.

The arbitrator is ONLY a communication conduit. Domain-specific data (project management, etc.) goes through its own specialist and storage provider.

### Project-Storage-Provider
Abstract CRUD API for dev-team-project data. Single entry point: `python3 scripts/project_storage.py <resource> <action> [--flags]`.

- Backend-swappable via `PROJECT_STORAGE_BACKEND` env var (default: `markdown`)
- Full CRUD: create, get, list (with filters), update, delete
- Resources: project, milestone, todo, issue, concern, dependency, decision

**Markdown backend**: stores items as markdown files with YAML frontmatter in `.dev-team-project/` directory. 64 contract tests in `tests/project-storage/`.

Called by the project-manager specialist, not by other components directly.

## Data Flow

### Communication (Arbitrator)
All participant-to-participant communication flows through the arbitrator:
- user ↔ team-lead (messages, gates, verdicts, notifications)
- team-lead ↔ specialist (assignments, results, state transitions)
- specialist ↔ specialty-team (findings, verifications, retries)

### Project Management (Project-Storage-Provider)
Project-manager specialist ↔ project-storage-provider ↔ `.dev-team-project/` directory

### Interaction Contract
5 message types between team-lead and user:

| Type | Direction | Description |
|------|-----------|-------------|
| Question | Lead → User | Open-ended, needs thoughtful answer |
| Answer | User → Lead | Response to a question |
| Gate | Lead → User | Options presented, work pauses until verdict |
| Verdict | User → Lead | Selected option from a gate |
| Notification | Lead → User | One-way status update |

Gate categories: flow (normal checkpoint), error (something broke), conflict (specialists disagree).
Notification severity: info, warning, error. Category: progress, result, briefing.

## Subcommands

| Command | Team-Lead | What It Does |
|---------|-----------|-------------|
| `interview` | interview | Discover product requirements through structured and exploratory questioning with specialist expertise |
| `create-recipe-from-code` | analysis | Reverse-engineer a codebase into a cookbook project |
| `generate` | review | Improve a cookbook project through specialist review |
| `create-code-from-recipe` | build | Build working code from a cookbook project |
| `lint` | audit | Evaluate any artifact against cookbook standards |
| `align-specialists` | audit | Review specialist-cookbook alignment after guideline changes |
| `compare-code` | analysis | Compare two code projects for round-trip verification |
| `view-recipe` | — | Generate HTML view of a cookbook project (read-only) |

## Configuration

**System config**: `~/.agentic-cookbook/dev-team/config.json`
```json
{
  "workspace_repo": "<path to workspace repo>",
  "cookbook_repo": "<path to agentic-cookbook>",
  "user_name": "<user name>",
  "authorized_repos": []
}
```

**Shared database**: `~/.agentic-cookbook/dev-team/dev-team.db` (SQLite). Schema v2 in progress — requirements doc at `docs/planning/2026-04-03-initial-database-design.md`, waiting on DB specialist.

## File Map

```
plugins/
  dev-team/                  # Self-enclosed plugin
    .claude-plugin/          # Plugin manifest
    agents/                  # 20 agent definitions
    specialists/             # 20 specialist definitions (13 domain + 6 platform + 1 PM)
    specialty-teams/         # 212 specialty-team files in 20 category dirs
    consulting-teams/         # Consulting-team files (cross-cutting verification)
    skills/
      dev-team/              # Single skill with subcommand routing
        SKILL.md             # Router (v0.6.0)
        workflows/           # One workflow file per subcommand
    scripts/
      arbitrator.py          # Communication conduit dispatcher
      arbitrator/markdown/   # Markdown arbitrator backend (13 resource scripts)
      project_storage.py     # Project management storage dispatcher
      project-storage/markdown/ # Markdown project-storage backend (8 scripts)
      db/                    # Database Python API
      observers/                # Observer modules (auto-discovered by SubagentStop hook)
        dispatch.py             # Hook entry point — event extraction + observer dispatch
        stenographer.py         # Session.log JSONL writer
        oslog.py                # System log writer (macOS/Linux)
      run_specialty_teams.py # Parses specialist manifests to JSON
      load_config.py         # Config loader
    services/
      dashboard/             # Live workflow dashboard (Flask, port 9876)
    docs/
      specialist-spec.md     # Formal specialist file specification
      specialist-guide.md    # How specialists and specialty-teams work
      research/              # Specialist assignment rules and mappings
    tests/
      test-mode-spec.md      # Test mode contract for workflows

# Development tooling (repo root)
.claude/                     # Claude Code local config, rules, dev skills
docs/
  architecture.md            # THIS FILE — single source of truth
  planning/                  # Design specs and decision history
  superpowers/               # Brainstorming specs and implementation plans
planning/                    # Temporary tracking (todo, cookbook requests)
tests/
  arbitrator/                # 68 contract tests for arbitrator API
  project-storage/           # 64 contract tests for project-storage API
  harness/                   # Vitest test harness
```

## Design Rules

- **DB schema**: `.claude/rules/db-schema-design.md` — no blobs, no counts, meaningful names, searchable columns
- **Specialist format**: `docs/specialist-spec.md` — required sections, manifest format, specialty-team file format
- **Performance**: Shell scripts for deterministic work, model selection for subagents, progressive disclosure
- **Storage abstraction**: Arbitrator for communication, project-storage-provider for PM data — both backend-swappable
- **Naming**: `-cookbook-project` suffix for code specs, verb-based commands, symmetric `create-X-from-Y`

## What's In Progress

See `planning/todo.md` for current status. Key items:
- DB schema finalization (waiting on specialist)
- Cookbook sources for project-manager (in progress)
- Recipe-reviewer disposition
- Absorbed agents cleanup (specialist-interviewer, specialist-code-pass)
- Wiring workflows to arbitrator
