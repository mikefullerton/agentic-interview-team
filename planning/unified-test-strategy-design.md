# Unified Test Strategy for All Skills and Agents

## Problem

The interview skill has a solid test infrastructure (Vitest, `claude -p` runner, personas, test-log.jsonl, E2E specs), but the other three skills (create-project-from-code, generate, build) have no test infrastructure. As the system grows, every skill and its agents need to be testable through a consistent, unified approach.

## Decisions

- **Test driver:** `claude -p` CLI invocation (same as interview), running real skills with real agent spawning
- **Test fixtures (for now):** Use Mike's real projects as test targets. Dedicated, constrained fixtures will be created later.
- **Approval simulation:** Auto-approve all prompts in test mode (no simulated-user agent needed for non-interview skills)
- **Log schema:** Unified across all skills — common base fields + skill-specific event types
- **Harness:** Extend the existing `tests/harness/` Vitest setup (don't build a new one)
- **Approach:** Shared test infrastructure layer — a `tests/test-mode-spec.md` document defines the common contract that all skills reference

## Architecture

### Shared Test Mode Contract (`tests/test-mode-spec.md`)

A specification document that all skills reference for their `--test-mode` behavior:

**Common flags:**
- `--test-mode` — activates automated testing
- `--target <path>` — specifies the input (repo path for analyze, cookbook project path for generate/build)
- `--config <path>` — path to test config (existing)
- `--max-exchanges <n>` — interview-specific, limits Q&A count

**Common behavior in test mode:**
- All `AskUserQuestion` calls are auto-approved — proceed with the first/default option
- Write `test-log.jsonl` to the project output directory
- No user profile updates
- Config must pre-exist (no setup flow)
- For interview only: use `simulated-user` agent with `--persona <path>` instead of real user

**Unified log schema:**
```jsonl
{"skill": "<skill-name>", "phase": "<phase-name>", "event": "<event-type>", "timestamp": "<ISO 8601>", ...event-specific-fields}
```

### Common Event Types (All Skills)

| Event | Fields | When |
|-------|--------|------|
| `phase_started` | `phase` | A skill phase begins |
| `phase_completed` | `phase`, `duration_ms` | A skill phase finishes |
| `agent_spawned` | `agent`, `recipe`? , `specialist`? | A subagent is launched |
| `agent_completed` | `agent`, `recipe`?, `specialist`?, `status` | A subagent returns |
| `file_written` | `path`, `type` (recipe, review, code, report, etc.) | An artifact is persisted |
| `error` | `phase`, `message`, `agent`?, `recoverable` | Something went wrong |
| `test_complete` | `phases_completed`, `agents_spawned`, `files_written`, `errors` | Final summary |

### Skill-Specific Event Types

#### interview
| Event | Fields |
|-------|--------|
| `specialist_invoked` | `specialist`, `mode` (structured/exploratory) |
| `question_asked` | `specialist`, `question_id` |
| `answer_received` | `transcript_file` |
| `analysis_written` | `analysis_file`, `transcript_id` |
| `checklist_updated` | `topic`, `action` (covered/discovered) |

#### analyze
| Event | Fields |
|-------|--------|
| `architecture_scanned` | `tech_stack`, `platforms`, `module_count` |
| `scopes_matched` | `count`, `high_confidence`, `medium_confidence`, `low_confidence` |
| `recipe_generated` | `scope`, `output_path`, `needs_review_count` |
| `project_assembled` | `component_count`, `manifest_path` |

#### generate
| Event | Fields |
|-------|--------|
| `reviewer_spawned` | `recipe_scope`, `specialist` |
| `review_completed` | `recipe_scope`, `specialist`, `suggestion_count`, `gap_count` |
| `suggestion_approved` | `recipe_scope`, `specialist`, `title` |
| `suggestion_rejected` | `recipe_scope`, `specialist`, `title` |
| `recipe_updated` | `recipe_scope`, `changes_applied`, `new_version` |

#### build
| Event | Fields |
|-------|--------|
| `scaffold_created` | `build_system`, `file_count`, `build_command` |
| `code_generated` | `recipe_scope`, `files_written`, `must_implemented`, `must_total` |
| `specialist_pass_complete` | `recipe_scope`, `specialist`, `changes_count` |
| `code_review_complete` | `recipe_scope`, `issues_found`, `issues_fixed` |
| `build_attempted` | `attempt`, `error_count`, `fixed_count` |
| `build_result` | `success`, `total_attempts`, `remaining_errors` |
| `smoke_test_result` | `launch_pass`, `conformance_passed`, `conformance_failed`, `conformance_skipped` |

## Test Cases

### create-project-from-code

**Smoke test** (`specs/create-project-from-code-smoke.test.ts`):
- Target: one of Mike's real repos
- Verify: architecture-map.md written, scope-report.md written, at least 1 recipe generated, cookbook-project.json created
- Timeout: 16 minutes

**Coverage test** (`specs/create-project-from-code-coverage.test.ts`):
- Target: one of Mike's repos with known tech stack
- Verify: scope-matcher finds scopes appropriate to the repo's tech stack (e.g., iOS repo gets `recipe.ui.*` scopes)
- Verify: recipe-writer generates recipes for all approved scopes

### generate

**Smoke test** (`specs/generate-smoke.test.ts`):
- Target: an existing cookbook project on disk (either from a prior create-project-from-code run or a pre-built fixture). The test config specifies the path via `TEST_TARGET_PROJECT` env var.
- Verify: at least 1 recipe reviewed, review files written, recipe versions bumped
- Timeout: 16 minutes

**Coverage test** (`specs/generate-coverage.test.ts`):
- Verify: specialist assignment matches recipe content (UI recipe gets UI/UX specialist)
- Verify: all assigned specialists produce reviews

### build

**Smoke test** (`specs/build-smoke.test.ts`):
- Target: an existing cookbook project on disk (same source as generate tests — path from `TEST_TARGET_PROJECT` env var)
- Verify: scaffold created, at least 1 recipe's code generated, build attempted
- Timeout: 30 minutes (builds take longer)

**Scaffold test** (`specs/build-scaffold.test.ts`):
- Verify: scaffolded project compiles on its own before any code generation
- Verify: correct build system detected for platform

**Specialist order test** (`specs/build-specialist-order.test.ts`):
- Verify: `specialist_pass_complete` events are in tier order (architecture before security before platform)
- Verify: each pass references the recipe it augmented

### Cross-skill pipeline test (future)

**Pipeline test** (`specs/pipeline.test.ts`):
- Run: analyze → generate → build on the same repo
- Verify: full pipeline produces output at each stage
- Verify: build's input is generate's output
- Deferred until individual skill tests are stable

## Harness Changes

### Existing modules to extend

**`lib/runner.ts`:**
- Add `runSkill(skillName: string, args: string[]): Promise<RunResult>` alongside existing `runInterview()`
- `runInterview()` becomes a thin wrapper around `runSkill("interview", ...)`
- `RunResult` includes: exit code, stdout, stderr, output directory path

**`lib/fixtures.ts`:**
- Add `getTargetRepo(): string` — reads target repo path from test config or `TEST_TARGET_REPO` env var
- Add `getTargetProject(): string` — reads cookbook project path for generate/build tests
- Add `createTestConfig(overrides)` — creates a test config file with paths to Mike's repos

**`lib/assertions.ts`:**
- Add skill-agnostic assertions:
  - `expectFileWritten(log, pathPattern)` — verify a `file_written` event matching pattern
  - `expectAgentSpawned(log, agentName)` — verify an `agent_spawned` event
  - `expectPhaseCompleted(log, phaseName)` — verify a phase ran to completion
  - `expectBuildResult(log, expected: "success" | "failure")` — verify build outcome
  - `expectSpecialistOrder(log, recipe, expectedOrder)` — verify tier ordering
- Keep existing interview-specific assertions unchanged

### New modules

**`lib/log-parser.ts`:**
- Parse unified `test-log.jsonl` format
- Return typed event arrays
- Filter by skill, phase, event type
- Backward-compatible: handle legacy interview log format too

### New test scripts in package.json

```json
{
  "test:create-project-from-code:smoke": "vitest run --config vitest.e2e.config.ts specs/create-project-from-code-smoke.test.ts",
  "test:generate:smoke": "vitest run --config vitest.e2e.config.ts specs/generate-smoke.test.ts",
  "test:build:smoke": "vitest run --config vitest.e2e.config.ts specs/build-smoke.test.ts",
  "test:all:smoke": "vitest run --config vitest.e2e.config.ts specs/*-smoke.test.ts"
}
```

## Skill Modifications

### All skills

Each skill's SKILL.md gets a new section:

```markdown
## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract at
`<interview_team_repo>/tests/test-mode-spec.md`.

Key behaviors:
- Auto-approve all `AskUserQuestion` prompts (proceed with first/default option)
- Write `test-log.jsonl` to the output directory with unified event schema
- Log events: <list of skill-specific events from the contract>
```

### interview (migration)

- Update existing test-log events to include `skill: "interview"` and `phase` fields
- Add the common event types (`phase_started`, `phase_completed`, `agent_spawned`, etc.)
- Keep `simulated-user` agent — interview is the only skill that needs it
- Update existing test assertions to handle the new field names (backward-compatible migration)

### analyze, generate, build

- Add `--test-mode` flag handling
- Add `--target <path>` flag for specifying input
- In test mode: skip `AskUserQuestion`, proceed with defaults
- Write unified test-log events at each phase boundary and agent interaction

## Implementation Order

1. Write `tests/test-mode-spec.md` (the shared contract)
2. Add `lib/log-parser.ts` to the harness
3. Extend `lib/runner.ts` with `runSkill()`
4. Extend `lib/assertions.ts` with skill-agnostic assertions
5. Add `--test-mode` to create-project-from-code SKILL.md
6. Write `specs/create-project-from-code-smoke.test.ts`
7. Add `--test-mode` to generate SKILL.md
8. Write `specs/generate-smoke.test.ts`
9. Add `--test-mode` to build SKILL.md
10. Write `specs/build-smoke.test.ts` and other build specs
11. Migrate interview's test-log format to unified schema
12. Update existing interview test assertions
13. Create dedicated test fixtures (future — replace real project targets)

## Future: Dedicated Test Fixtures

When ready to replace real project targets with constrained fixtures:
- Create minimal repos (2-3 files each) targeting specific platforms
- Derive from interview personas (Sarah's iOS app, Marcus's SaaS, Priya's marketplace)
- Store in `tests/fixtures/repos/` (small, committed to the repo)
- Store pre-built cookbook projects in `tests/fixtures/projects/` (output of analyze on fixture repos)
- Each fixture designed to exercise specific code paths (iOS scaffolding, multi-platform, empty repo edge case)
