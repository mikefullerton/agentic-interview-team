# Dev-Team Project — Research & Design

## Context

A dev-team-project is a **project management** artifact — schedules, todos, issues, concerns, dependencies, decisions. It is NOT a technical specification (that's a cookbook-project). One dev-team-project can manage multiple cookbook-projects.

The project-manager is a specialist (like security or accessibility) with specialty-teams for each aspect of project management. It interacts with the dev-team through the same channels as any other specialist.

## Architecture

```
project-manager (specialist)
    ↕
project-storage-provider (abstract API / protocol)
    ↕
markdown-project-storage-provider (first implementation)
    → writes .dev-team-project/ directory in git
```

- **project-manager** — specialist with specialty-teams for schedule, todos, issues, concerns, dependencies, decisions
- **project-storage-provider** — abstract API definition. Looks like a structured DB. Full CRUD. The project-manager calls this, never knows the implementation.
- **markdown-project-storage-provider** — first implementation. Writes markdown files to `.dev-team-project/` in the user's git repo.

## Item Types

### Manifest
Project-level metadata.
- **name**: project name
- **description**: what this project is
- **created**: when it was created
- **cookbook_projects**: list of linked cookbook-project paths

### Milestone
A target in the schedule.
- **name**: milestone identifier
- **description**: what this milestone represents
- **target_date**: when it should be done
- **status**: planned, in-progress, completed, missed
- **dependencies**: which milestones must complete first

### Todo
A task to be done.
- **title**: short description
- **description**: what needs to be done
- **assignee**: who's responsible (team-lead, specialist, user)
- **priority**: critical, high, medium, low
- **status**: open, in-progress, done, blocked
- **milestone**: which milestone this belongs to
- **blocked_by**: what's blocking this

### Issue
A problem, blocker, or risk.
- **title**: short description
- **description**: what's wrong
- **severity**: critical, major, minor
- **status**: open, investigating, resolved, wontfix
- **source**: where this came from (specialist:security, interview, build)
- **related_findings**: finding IDs from the arbitrator

### Concern
Something needing attention that isn't a blocker yet.
- **title**: short description
- **description**: what needs attention
- **raised_by**: who flagged it
- **status**: open, addressed, dismissed
- **related_to**: what this concerns

### Dependency
Something this project depends on.
- **name**: what the dependency is
- **type**: internal (between cookbook-projects/components) or external (third-party)
- **description**: why this dependency exists
- **status**: available, pending, blocked, at-risk

### Decision
A choice that was made.
- **title**: what was decided
- **description**: the full context
- **rationale**: why this choice was made
- **alternatives**: what was considered and rejected
- **made_by**: who decided (user, team-lead, specialist)
- **date**: when it was decided

## Project-Storage-Provider API

Abstract interface. All implementations must support these operations. Looks like a structured DB — CRUD on typed items with filtering.

### Project lifecycle
```
project-storage init --name <name> --description <text> --path <path>
project-storage status
project-storage link-cookbook --path <cookbook-project-path>
project-storage unlink-cookbook --path <cookbook-project-path>
```

### Item CRUD
```
project-storage create <type> --field value [--field value ...]
project-storage get <type> --id <id>
project-storage list <type> [--status <status>] [--priority <priority>] [--milestone <name>] [--severity <severity>]
project-storage update <type> --id <id> --field value [--field value ...]
project-storage delete <type> --id <id>
```

Where `<type>` is: milestone, todo, issue, concern, dependency, decision

### Conventions
- All commands output JSON to stdout, errors to stderr, exit 0/1
- IDs are opaque strings
- Filters are optional, combinable
- Update only changes specified fields, leaves others untouched

## Markdown Implementation

### Directory structure

```
.dev-team-project/
  manifest.json
  schedule/
    <id>-<name-slug>.md
  todos/
    <id>-<title-slug>.md
  issues/
    <id>-<title-slug>.md
  concerns/
    <id>-<title-slug>.md
  dependencies/
    <id>-<name-slug>.md
  decisions/
    <id>-<title-slug>.md
```

### File format

Each item is a markdown file with YAML frontmatter for structured fields:

```markdown
---
id: todo-0001
title: Implement CSRF protection
status: open
priority: critical
assignee: specialist:security
milestone: security-hardening
blocked_by: null
created: 2026-04-04
modified: 2026-04-04
---

Implement CSRF token validation on all form submissions. The security
specialist identified this as a critical gap during the generate review.

Related findings: session-abc:finding:security:0003
```

Frontmatter = structured, queryable fields. Body = description (free-form markdown for LLM consumption).

### Querying

The markdown provider reads frontmatter to filter. `list todo --status open --priority critical` reads all files in `todos/`, parses frontmatter, filters by status and priority, returns matching items as JSON array.

### Updates

`update todo --id todo-0001 --status done` reads the file, modifies the frontmatter field, updates `modified` date, writes back.

### Script layout

```
scripts/
  project-storage.sh                       # dispatcher (like arbitrator.sh)
  project-storage/
    markdown/
      _lib.sh                              # shared helpers
      project.sh                           # init, status, link/unlink cookbook
      milestone.sh
      todo.sh
      issue.sh
      concern.sh
      dependency.sh
      decision.sh
```

## Project-Manager Specialist

A new specialist definition at `specialists/project-manager.md` with specialty-teams:

| Specialty-Team | Artifact | Focus |
|---------------|----------|-------|
| schedule | .dev-team-project/schedule/ | Milestones, phases, deadlines, sequencing |
| todos | .dev-team-project/todos/ | Task breakdown, assignment, prioritization |
| issues | .dev-team-project/issues/ | Problem identification, triage, resolution tracking |
| concerns | .dev-team-project/concerns/ | Risk identification, attention flagging |
| dependencies | .dev-team-project/dependencies/ | Internal/external dependency mapping and status |
| decisions | .dev-team-project/decisions/ | Decision recording, rationale, alternatives |

## Test Strategy

Same pattern as the arbitrator: backend-agnostic contract tests that validate the project-storage-provider API regardless of implementation.

```
tests/
  project-storage/
    run-contract-tests.sh
    lib/
      test-helpers.sh
    contract/
      01-project-lifecycle.sh
      02-milestones.sh
      03-todos.sh
      04-issues.sh
      05-concerns.sh
      06-dependencies.sh
      07-decisions.sh
      08-updates-and-deletes.sh
      09-filtering.sh
      10-error-handling.sh
```
