# Plan: System Terminology & Component Architecture

> **Status:** Superseded by [`2026-04-11-conductor-architecture.md`](./2026-04-11-conductor-architecture.md). This doc captured the first DB-centric rearchitecture pass, which assumed the team-lead runs in the user's Claude Code conversation. The April 11 doc pushes the outer loop out of Claude entirely (headless conductor + `claude -p` subprocess dispatch). Read v2 for terminology foundations and the disposition table; read the April 11 doc for the current target architecture.

## Context

The dev-team system has accumulated overlapping names and an architecture where components pass data through agent return values and markdown strings. We're redesigning with clear terminology, DB-centric communication, and self-enclosed specialists.

## Agreed Terminology

| Term | Definition |
|---|---|
| **Team-Lead** | Runs a workflow, has a persona, talks to the user. Types: interview-lead, analysis-lead, review-lead, build-lead, audit-lead. |
| **Playbook** | Static definition of a workflow — which team-lead, which specialists, phases, inputs, outputs. |
| **Workflow** | A playbook being executed — runtime instance with state, tracked in DB as a session. |
| **Specialist** | Self-enclosed component: deterministic script that runs specialist-teams, collects findings, invokes the specialist-persona. Returns report_id + pass/fail to team-lead. |
| **Specialist-Team** | A specialty-worker / specialty-verifier pair focused on one cookbook artifact. |
| **Specialty-Worker** | LLM agent. Reads one cookbook artifact, produces structured findings. Isolated — never sees verifier instructions. |
| **Specialty-Verifier** | LLM agent. Checks specialty-worker output for completeness. Returns PASS/FAIL. Isolated — never sees worker instructions. |
| **Specialist-Persona** | LLM agent. Reads raw findings from DB + persona definition, writes persona-voiced interpretation rows to DB. Translation layer only — produces no new findings. |
| **Specialist Report** | The packaged result: raw findings + verification summary + persona interpretation. Stored in DB, referenced by report_id. |

## Pre-existing Agents — Disposition

| Agent | Decision |
|---|---|
| `specialist-interviewer.md` | Absorbed into specialty-worker (interview mode) |
| `specialist-code-pass.md` | Absorbed — domain knowledge moves into specialist definitions, tier ordering is a build team-lead / playbook concern |
| `recipe-reviewer.md` | TBD — revisiting later |
| `transcript-analyzer.md` | Part of the interview team-lead's toolset |
| `specialist-aligner.md` | Stays as utility agent for align-specialists skill |

## Architecture — DB-Centric Communication

All communication flows through the database. No large markdown or JSON passing between components. Components read assignments from DB, write results to DB, pass only row IDs and pass/fail status upward.

### Data Flow

```
Team-Lead writes assignment to DB
  → Specialist script reads assignment
    → Script writes specialist-team assignments to DB
      → Specialty-worker reads assignment from DB, writes findings to DB
      → Specialty-verifier reads findings from DB, writes verdict to DB
      → If FAIL and retries < 3: script writes retry, worker reads and writes
    → After all teams: Specialist-persona reads findings from DB, writes interpretation to DB
  → Specialist script writes final status to DB
← Team-Lead reads: { report_id, passed }
```

### Persona Interpretation Rows

Lightweight foreign-key reference, not a full transcript copy:

| id | source_row_id | specialist | interpretation |
|---|---|---|---|
| 101 | 42 | security | "Your token lifetime is the problem..." |

The specialist-persona only writes interpretations for findings that need explaining.

### Team-Lead Interface

The team-lead's interface to a specialist is minimal:

```
Request:  "security, analyze this target"  (written to DB)
Response: { report_id: 42, passed: true }
```

If the team-lead needs detail, it queries the DB by report_id. If the user wants to drill in, follow foreign keys deeper.

## Session Management

### `sessions` table — immutable metadata, one row per session:
- id, created, machine, user, working_directory
- cookbook_repo, workspace_repo
- playbook, team_lead, target
- status (running, completed, failed, interrupted)
- started_at, ended_at

### `session_state` table — append-only state transitions:
- id, session_id (FK → sessions), timestamp
- component (team-lead, specialist:security, specialist-team:authentication, specialty-worker, specialty-verifier, specialist-persona)
- state (pending, running, completed, failed, escalated)
- detail (JSON — error message, retry count, report_id, etc.)

Every component writes state transitions. Latest row per component = current state. On crash, the DB shows exactly where it stopped. Resumability: new session reads previous session_state, picks up from first non-completed step. Completed findings already persisted — no rework.

### Relationship to existing tables

The existing `workflow_runs` → evolves into `sessions`. The existing `agent_runs` → evolves into `session_state`. Existing `findings`, `artifacts`, `messages` tables stay but become children of sessions via foreign keys.

## Failure Handling

| Failure Type | Who Handles | What Happens |
|---|---|---|
| Specialty-verifier says FAIL | Specialist script | Normal loop — retry up to 3, then escalate |
| Agent crash (context limit, timeout) | Specialist script | Writes failed state to session_state, returns error to team-lead |
| Missing cookbook artifact | Specialty-worker | Writes finding with status "error", specialist script surfaces it |
| Missing target file | Specialist script | Catches before dispatching, writes error to session_state |
| DB write failure | Calling component | Fatal — surfaces immediately to team-lead |
| User interrupts | Session | Status set to "interrupted", resumable from last completed step |

Team-lead decides what to tell the user: retry, skip, or stop.

## Interaction Contract

The team-lead is the only component that talks to the user. All communication uses these message types:

### Message Types

| Type | Direction | Description |
|---|---|---|
| **Question** | Lead → User | Open-ended, needs thoughtful answer |
| **Answer** | User → Lead | Response to a question |
| **Gate** | Lead → User | Options presented, work pauses until verdict |
| **Verdict** | User → Lead | Selected option from a gate |
| **Notification** | Lead → User | One-way status update, no response needed |

### Gate Attributes

| Attribute | Values | Description |
|---|---|---|
| category | flow, error, conflict | Why the gate is being presented |
| options | list | Available choices |
| default | string | Pre-selected option if user just confirms |

- **flow** — normal checkpoint (assignment approval, suggestion approve/reject)
- **error** — something broke (retry, skip, abort)
- **conflict** — specialists disagree (pick a direction)

### Notification Attributes

| Attribute | Values | Description |
|---|---|---|
| severity | info, warning, error | How urgent |
| category | progress, result, briefing | What kind of update |

### Detail Levels

- Pass with no issues → notification (info/result): "Security passed."
- Fail → notification (warning/result) + gate (error): pull specialist-persona interpretation for failed findings, present options
- User drills in → team-lead queries DB for raw findings

All messages are written to the DB as part of the session transcript.

## Additional Decisions

- **User** — just "user", no special term needed
- **Artifact** — a specialist-team's artifact can be one or more tightly coupled cookbook files (guideline + compliance, etc.). Comma-separated backtick-wrapped paths. Parser needs updating.
- **Artifact optimization** — potential future pass to pre-optimize cookbook artifacts for LLM consumption. Revisit later.

## Still To Discuss

- Recipe-reviewer disposition
- DB schema details (evolve existing tables vs new tables)
- Playbook file format
- Specialist script design (extend run-specialty-teams.sh or new script)
- Rename pass across all existing files to align with new terminology
