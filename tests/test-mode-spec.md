# Test Mode Contract v1.1

All skills in the dev-team plugin support `--test-mode` for automated testing. This document is the single source of truth for test mode behavior. Skills reference this file instead of inlining test mode details.

## How Skills Reference This Contract

Each skill's Test Mode section should say:

> When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract at `${CLAUDE_PLUGIN_ROOT}/tests/test-mode-spec.md`.
> Read the contract file at the start of test mode to understand the unified log schema and skill-specific behaviors.

Skills should NOT inline test mode behavior — this file defines it all.

## Common Flags

- `--test-mode` — activates automated testing mode
- `--target <path>` — specifies the input (see per-skill target semantics below)
- `--config <path>` — path to test config file (must pre-exist, no setup flow)

### Interview-specific flags
- `--persona <path>` — path to a persona file for the simulated user
- `--max-exchanges <n>` — stop after N question-answer exchanges

## Common Behavior

When `--test-mode` is active:

1. **Auto-approve all prompts.** Every `AskUserQuestion` call is auto-approved — proceed with the first/default option. Do not wait for user input. See per-skill auto-approve policies below for skill-specific details.
2. **Exception: interview skill.** The interview skill uses the `simulated-user` agent with `--persona <path>` instead of auto-approve, since it needs realistic conversational answers.
3. **Write test log.** Write structured events to `test-log.jsonl` in the project output directory (see per-skill log location below). One JSON object per line.
4. **No profile updates.** Don't modify user profiles or persist learning — test data is ephemeral.
5. **Config must pre-exist.** If the config file doesn't exist at the `--config` path, fail immediately with a clear error.
6. **Bounded execution.** For interview: stop after `--max-exchanges`. For other skills: run to completion.

## Target Semantics Per Skill

The `--target <path>` flag (or first positional arg) meaning varies by skill:

| Skill | `--target` points to | Required in test mode? |
|-------|---------------------|----------------------|
| interview | N/A (uses `--persona` and `--config` instead) | No |
| analyze | Repository path to analyze | Yes |
| generate | Cookbook project directory (containing `cookbook-project.json`) | Yes |
| build | Cookbook project directory (containing `cookbook-project.json`) | Yes |
| lint | Artifact path (file or directory to lint) | Yes |

## Test Log Location Per Skill

| Skill | `test-log.jsonl` location |
|-------|--------------------------|
| interview | `<workspace_repo>/projects/<project>/test-log.jsonl` |
| analyze | `<output>/test-log.jsonl` |
| generate | `<project>/test-log.jsonl` |
| build | `<output>/test-log.jsonl` |
| lint | Current working directory |

## Auto-Approve Policies Per Skill

All skills auto-approve AskUserQuestion prompts with the first/default option. Some skills have specific policies for particular prompts:

### interview
- No AskUserQuestion auto-approve — uses `simulated-user` agent instead

### analyze
- Architecture scan confirmation ("Does this look right?") — auto-approve
- Scope approval ("Want to add or remove any scopes?") — auto-approve
- Overwrite confirmation ("A project already exists...") — auto-approve

### generate
- Specialist assignment approval ("Want to adjust before I start reviews?") — auto-approve
- Individual suggestion approval — **approve all suggestions**
- Question answering — **skip all questions** (don't answer, mark as skipped)

### build
- Specialist assignment approval — auto-approve
- Scaffold confirmation — auto-approve
- Code review fix approval — **approve all fixes**
- Build failure options — **choose "try more fixes" up to 2 extra attempts, then "skip to smoke tests"**
- Resumability check — **choose "regenerate all"**

### lint
- Specialist assignment acknowledgment — auto-approve
- Individual fix approval — **approve all suggestions**
- Compliance fix approval — **approve all suggestions**

## Unified Log Schema

Every log line is a JSON object with these base fields:

```json
{
  "skill": "<skill-name>",
  "phase": "<phase-name>",
  "event": "<event-type>",
  "timestamp": "<ISO 8601>"
}
```

Plus event-specific fields documented below.

### Common Events (All Skills)

| Event | Additional Fields | When |
|-------|------------------|------|
| `phase_started` | — | A skill phase begins |
| `phase_completed` | `duration_ms` | A skill phase finishes |
| `agent_spawned` | `agent`, `recipe`?, `specialist`? | A subagent is launched |
| `agent_completed` | `agent`, `recipe`?, `specialist`?, `status` | A subagent returns |
| `file_written` | `path`, `file_type` | An artifact is persisted |
| `error` | `message`, `agent`?, `recoverable` | Something went wrong |
| `test_complete` | `phases_completed`, `agents_spawned`, `files_written`, `errors` | Final summary |

## Per-Skill Phases and Agents

### interview

**Phases:** `startup`, `interview-loop`, `summary`

**Agents:** `transcript-analyzer`, `specialist-interviewer`, `specialist-analyst`, `simulated-user`

### analyze

**Phases:** `architecture-scan`, `scope-discovery`, `recipe-generation`, `project-assembly`, `summary`

**Agents:** `codebase-scanner`, `scope-matcher`, `recipe-writer`, `project-assembler`

### generate

**Phases:** `load-project`, `specialist-assignment`, `review-loop`, `final-report`

**Agents:** `recipe-reviewer` (one instance per specialist per recipe)

### build

**Phases:** `load-project`, `specialist-assignment`, `scaffolding`, `code-generation`, `code-review`, `build`, `smoke-test`, `final-report`

**Agents:** `project-scaffolder`, `code-generator`, `specialist-code-pass`, `build-runner`, `smoke-tester`

### lint

**Phases:** `resolve-target`, `specialist-assignment`, `review`, `present-results`, `apply-fixes`, `compliance-only`

**Agents:** `artifact-reviewer` (one instance per specialist)

## Per-Skill Events

### interview Events

| Event | Additional Fields |
|-------|------------------|
| `specialist_invoked` | `specialist`, `mode` |
| `question_asked` | `specialist`, `question_id` |
| `answer_received` | `transcript_file` |
| `analysis_written` | `analysis_file`, `transcript_id` |
| `checklist_updated` | `topic`, `action` |

### analyze Events

| Event | Additional Fields |
|-------|------------------|
| `architecture_scanned` | `tech_stack`, `platforms`, `module_count` |
| `scopes_matched` | `count`, `high_confidence`, `medium_confidence`, `low_confidence` |
| `recipe_generated` | `scope`, `output_path`, `needs_review_count` |
| `project_assembled` | `component_count`, `manifest_path` |

### generate Events

| Event | Additional Fields |
|-------|------------------|
| `reviewer_spawned` | `recipe_scope`, `specialist` |
| `review_completed` | `recipe_scope`, `specialist`, `suggestion_count`, `gap_count` |
| `suggestion_approved` | `recipe_scope`, `specialist`, `title` |
| `suggestion_rejected` | `recipe_scope`, `specialist`, `title` |
| `recipe_updated` | `recipe_scope`, `changes_applied`, `new_version` |

### build Events

| Event | Additional Fields |
|-------|------------------|
| `scaffold_created` | `build_system`, `file_count`, `build_command` |
| `code_generated` | `recipe_scope`, `files_written`, `must_implemented`, `must_total` |
| `specialist_pass_complete` | `recipe_scope`, `specialist`, `changes_count` |
| `code_review_complete` | `recipe_scope`, `issues_found`, `issues_fixed` |
| `build_attempted` | `attempt`, `error_count`, `fixed_count` |
| `build_result` | `success`, `total_attempts`, `remaining_errors` |
| `smoke_test_result` | `launch_pass`, `conformance_passed`, `conformance_failed`, `conformance_skipped` |

### lint Events

| Event | Additional Fields |
|-------|------------------|
| `reviewer_spawned` | `artifact_path`, `specialist` |
| `review_completed` | `artifact_path`, `specialist`, `pass_count`, `warn_count`, `fail_count` |
| `fix_approved` | `check_id`, `specialist`, `title` |
| `fix_applied` | `artifact_path`, `check_id`, `description` |

The lint `test_complete` event includes additional fields: `pass_count`, `warn_count`, `fail_count`, `fixes_applied`, `verdict`.

## How to Emit Events

Skills write test log events by appending a JSON line to `test-log.jsonl` using the Write tool. Example:

At each phase boundary:
- Before starting Phase 1: write `{"skill": "analyze", "phase": "architecture-scan", "event": "phase_started", "timestamp": "<now>"}`
- After completing Phase 1: write `{"skill": "analyze", "phase": "architecture-scan", "event": "phase_completed", "duration_ms": <elapsed>, "timestamp": "<now>"}`

At each agent interaction:
- Before spawning: write `{"skill": "analyze", "phase": "architecture-scan", "event": "agent_spawned", "agent": "codebase-scanner", "timestamp": "<now>"}`
- After return: write `{"skill": "analyze", "phase": "architecture-scan", "event": "agent_completed", "agent": "codebase-scanner", "status": "success", "timestamp": "<now>"}`

At each file write:
- After persisting: write `{"skill": "analyze", "phase": "recipe-generation", "event": "file_written", "path": "app/ui/file-tree-browser.md", "file_type": "recipe", "timestamp": "<now>"}`

At the end:
- Write `{"skill": "analyze", "phase": "summary", "event": "test_complete", "phases_completed": 5, "agents_spawned": 8, "files_written": 12, "errors": 0, "timestamp": "<now>"}`
