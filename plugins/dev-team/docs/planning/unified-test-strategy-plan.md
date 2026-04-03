# Unified Test Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--test-mode` with unified test logging to all four skills (interview, create-project-from-code, generate, build) and extend the Vitest harness with specs for each.

**Architecture:** A shared test-mode contract (`tests/test-mode-spec.md`) defines common behavior and log schema. Each skill references it. The existing Vitest harness in `tests/harness/` is extended with a generic `runSkill()` function, a unified log parser, and skill-agnostic assertions. New E2E specs verify each skill's output.

**Tech Stack:** Vitest 3.2, TypeScript, `claude -p` CLI invocation

---

### Task 1: Write the shared test-mode contract

**Files:**
- Create: `tests/test-mode-spec.md`

- [ ] **Step 1: Create the test-mode spec**

```markdown
# Test Mode Contract v1.0

All skills in the agentic interview team support `--test-mode` for automated testing. This document defines the shared contract that all skills follow.

## Common Flags

- `--test-mode` — activates automated testing mode
- `--target <path>` — specifies the input (repo path for analyze, cookbook project path for generate/build)
- `--config <path>` — path to test config file (must pre-exist, no setup flow)

### Interview-specific flags
- `--persona <path>` — path to a persona file for the simulated user
- `--max-exchanges <n>` — stop after N question-answer exchanges

## Common Behavior

When `--test-mode` is active:

1. **Auto-approve all prompts.** Every `AskUserQuestion` call is auto-approved — proceed with the first/default option. Do not wait for user input.
2. **Exception: interview skill.** The interview skill uses the `simulated-user` agent with `--persona <path>` instead of auto-approve, since it needs realistic conversational answers.
3. **Write test log.** Write structured events to `test-log.jsonl` in the project output directory. One JSON object per line.
4. **No profile updates.** Don't modify user profiles or persist learning — test data is ephemeral.
5. **Config must pre-exist.** If the config file doesn't exist at the `--config` path, fail immediately with a clear error.
6. **Bounded execution.** For interview: stop after `--max-exchanges`. For other skills: run to completion.

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

## How to Emit Events

Skills write test log events by appending a JSON line to `test-log.jsonl` in the project output directory using the Write tool. Example:

At each phase boundary:
- Before starting Phase 1: write `{"skill": "create-project-from-code", "phase": "architecture-scan", "event": "phase_started", "timestamp": "<now>"}`
- After completing Phase 1: write `{"skill": "create-project-from-code", "phase": "architecture-scan", "event": "phase_completed", "duration_ms": <elapsed>, "timestamp": "<now>"}`

At each agent interaction:
- Before spawning: write `{"skill": "create-project-from-code", "phase": "architecture-scan", "event": "agent_spawned", "agent": "codebase-scanner", "timestamp": "<now>"}`
- After return: write `{"skill": "create-project-from-code", "phase": "architecture-scan", "event": "agent_completed", "agent": "codebase-scanner", "status": "success", "timestamp": "<now>"}`

At each file write:
- After persisting: write `{"skill": "create-project-from-code", "phase": "recipe-generation", "event": "file_written", "path": "app/ui/file-tree-browser.md", "file_type": "recipe", "timestamp": "<now>"}`

At the end:
- Write `{"skill": "create-project-from-code", "phase": "summary", "event": "test_complete", "phases_completed": 5, "agents_spawned": 8, "files_written": 12, "errors": 0, "timestamp": "<now>"}`
```

Write this to `tests/test-mode-spec.md`.

- [ ] **Step 2: Commit**

```bash
git add tests/test-mode-spec.md
git commit -m "Add shared test-mode contract for all skills"
git push
```

---

### Task 2: Create the unified log parser

**Files:**
- Create: `tests/harness/lib/log-parser.ts`

- [ ] **Step 1: Write the log parser module**

```typescript
/**
 * Unified test-log.jsonl parser.
 *
 * Parses the unified log schema (skill + phase + event + timestamp)
 * and the legacy interview format (event + timestamp, no skill/phase).
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";

/** Base fields present on every unified log event. */
export interface BaseLogEvent {
  skill: string;
  phase: string;
  event: string;
  timestamp: string;
  [key: string]: unknown;
}

/** Legacy interview log event (no skill/phase fields). */
export interface LegacyLogEvent {
  event: string;
  timestamp: string;
  [key: string]: unknown;
}

export type LogEvent = BaseLogEvent;

/**
 * Parse a test-log.jsonl file. Handles both unified and legacy formats.
 * Legacy events (missing skill/phase) are normalized with
 * skill="interview" and phase="unknown".
 */
export function parseLog(dir: string, relativePath = "test-log.jsonl"): LogEvent[] {
  const fullPath = join(dir, relativePath);
  if (!existsSync(fullPath)) return [];

  const content = readFileSync(fullPath, "utf-8");
  return content
    .trim()
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const parsed = JSON.parse(line);
      // Normalize legacy format
      if (!parsed.skill) {
        parsed.skill = "interview";
      }
      if (!parsed.phase) {
        parsed.phase = "unknown";
      }
      return parsed as LogEvent;
    });
}

/** Filter events by skill name. */
export function filterBySkill(events: LogEvent[], skill: string): LogEvent[] {
  return events.filter((e) => e.skill === skill);
}

/** Filter events by phase name. */
export function filterByPhase(events: LogEvent[], phase: string): LogEvent[] {
  return events.filter((e) => e.phase === phase);
}

/** Filter events by event type. */
export function filterByEvent(events: LogEvent[], event: string): LogEvent[] {
  return events.filter((e) => e.event === event);
}

/** Get all unique agent names that were spawned. */
export function agentsSpawned(events: LogEvent[]): string[] {
  return [
    ...new Set(
      filterByEvent(events, "agent_spawned").map((e) => e.agent as string)
    ),
  ];
}

/** Get all unique specialists that had passes. */
export function specialistsPassed(events: LogEvent[]): string[] {
  return [
    ...new Set(
      filterByEvent(events, "specialist_pass_complete").map(
        (e) => e.specialist as string
      )
    ),
  ];
}

/** Get all file_written events. */
export function filesWritten(events: LogEvent[]): LogEvent[] {
  return filterByEvent(events, "file_written");
}

/** Get all phases that completed. */
export function phasesCompleted(events: LogEvent[]): string[] {
  return filterByEvent(events, "phase_completed").map((e) => e.phase);
}

/** Get the test_complete summary event, if present. */
export function testSummary(events: LogEvent[]): LogEvent | undefined {
  return filterByEvent(events, "test_complete")[0];
}
```

Write this to `tests/harness/lib/log-parser.ts`.

- [ ] **Step 2: Commit**

```bash
git add tests/harness/lib/log-parser.ts
git commit -m "Add unified test-log parser with legacy format support"
git push
```

---

### Task 3: Extend the runner with `runSkill()`

**Files:**
- Modify: `tests/harness/lib/runner.ts`

- [ ] **Step 1: Add the `SkillRunOptions` interface and `runSkill()` function**

Add after the existing `runInterview` function (do not remove `runInterview` — it still works):

```typescript
export interface SkillRunOptions {
  /** Skill name — matches the directory name under skills/ */
  skillName: string;
  /** Working directory for the claude invocation */
  cwd: string;
  /** Path to the test config file */
  configPath: string;
  /** Target path — repo for analyze, cookbook project for generate/build */
  targetPath: string;
  /** Additional arguments to pass to the skill */
  extraArgs?: string[];
  /** Timeout in ms (default: 10 minutes) */
  timeout?: number;
}

/**
 * Run any skill in test mode via `claude -p`.
 *
 * Reads the skill's SKILL.md, strips frontmatter, substitutes variables,
 * and invokes via the CLI with --test-mode.
 */
export async function runSkill(opts: SkillRunOptions): Promise<RunResult> {
  const timeout = opts.timeout ?? DEFAULT_TIMEOUT;
  const configAbsolute = resolve(opts.configPath);
  const targetAbsolute = resolve(opts.targetPath);
  const root = repoRoot();

  // Set up harness log
  const logDir = join(root, "tests/harness/.logs");
  if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });
  const logFile = join(logDir, `run-${opts.skillName}-${Date.now()}.log`);

  log(logFile, `=== ${opts.skillName} Test Run ===`);
  log(logFile, `cwd: ${opts.cwd}`);
  log(logFile, `config: ${configAbsolute}`);
  log(logFile, `target: ${targetAbsolute}`);
  log(logFile, `repoRoot: ${root}`);

  // Read SKILL.md and strip YAML frontmatter
  const skillPath = join(root, `skills/${opts.skillName}/SKILL.md`);
  log(logFile, `Reading skill from: ${skillPath}`);
  let skillContent = readFileSync(skillPath, "utf-8");

  const fmMatch = skillContent.match(/^---\n[\s\S]*?\n---\n/);
  if (fmMatch) {
    log(logFile, `Stripping frontmatter (${fmMatch[0].length} chars)`);
    skillContent = skillContent.slice(fmMatch[0].length);
  }

  // Build the arguments string
  const argParts = [
    targetAbsolute,
    "--test-mode",
    `--config ${configAbsolute}`,
    ...(opts.extraArgs ?? []),
  ];
  const argsString = argParts.join(" ");
  log(logFile, `Arguments: ${argsString}`);

  // Substitute variables
  const skillDir = join(root, `skills/${opts.skillName}`);
  let prompt = skillContent
    .replace(/\$ARGUMENTS/g, argsString)
    .replace(/\$\{ARGUMENTS\}/g, argsString)
    .replace(/\$CLAUDE_SKILL_DIR/g, skillDir)
    .replace(/\$\{CLAUDE_SKILL_DIR\}/g, skillDir);

  // Append execution instruction
  prompt += `\n\n---\n\n## EXECUTE NOW\n\nYou are running in test mode. Execute the skill above immediately with these arguments: ${argsString}\n\nThe interview team repo is at: ${root}\nThe skill directory is at: ${skillDir}\n\nIMPORTANT: You MUST:\n1. Read the config file at ${configAbsolute}\n2. Follow the test mode contract at ${root}/tests/test-mode-spec.md\n3. Auto-approve all AskUserQuestion prompts (proceed with first/default option)\n4. Write test-log.jsonl with unified event schema\n5. Run all phases to completion\n\nStart by reading the config file NOW.\n`;

  log(logFile, `Prompt length: ${prompt.length} chars`);

  const args = [
    "-p", prompt,
    "--output-format", "json",
    "--dangerously-skip-permissions",
    "--max-turns", "80",
  ];

  log(logFile, `Launching claude with args: ${args.filter(a => a !== prompt).join(" ")}`);
  log(logFile, "Waiting for claude to complete...");

  return new Promise((resolvePromise) => {
    const proc = execFile(
      "claude",
      args,
      {
        cwd: opts.cwd,
        timeout,
        maxBuffer: 1024 * 1024 * 10,
        env: {
          ...process.env,
          CLAUDE_SKILL_DIR: skillDir,
        },
      },
      (error, stdout, stderr) => {
        log(logFile, `claude exited. error: ${error?.message ?? "none"}, code: ${error?.code ?? "0"}`);
        log(logFile, `stdout length: ${stdout?.length ?? 0}`);
        log(logFile, `stderr length: ${stderr?.length ?? 0}`);

        if (stderr) log(logFile, `STDERR:\n${stderr.slice(0, 2000)}`);
        if (stdout) log(logFile, `STDOUT (first 2000 chars):\n${stdout.slice(0, 2000)}`);

        if (error && !stdout) {
          log(logFile, `FAILED: ${error.message}`);
          resolvePromise({
            output: stderr || error.message,
            exitCode: typeof error.code === "number" ? error.code : 1,
            raw: stdout || "",
          });
          return;
        }

        try {
          const parsed = JSON.parse(stdout);
          log(logFile, `Parsed JSON output. result length: ${parsed.result?.length ?? 0}`);
          resolvePromise({
            output: parsed.result ?? "",
            exitCode: 0,
            raw: stdout,
          });
        } catch {
          log(logFile, `Could not parse JSON. Raw output used.`);
          resolvePromise({
            output: stdout || stderr || "",
            exitCode: typeof error?.code === "number" ? error.code : 0,
            raw: stdout,
          });
        }
      }
    );
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add tests/harness/lib/runner.ts
git commit -m "Add runSkill() for running any skill in test mode via CLI"
git push
```

---

### Task 4: Extend assertions with skill-agnostic helpers

**Files:**
- Modify: `tests/harness/lib/assertions.ts`

- [ ] **Step 1: Add import for log-parser at the top of the file**

Add this import at the top of `tests/harness/lib/assertions.ts` alongside the existing imports:

```typescript
import type { LogEvent } from "./log-parser.js";
import { filterByEvent } from "./log-parser.js";
```

- [ ] **Step 2: Add unified log assertions at the end of the file**

Add these functions at the end of `tests/harness/lib/assertions.ts`, after the existing interview-specific functions:

```typescript
// ── Unified log assertions (all skills) ───────────────────────────────

/**
 * Verify a file_written event exists matching a path pattern.
 */
export function expectFileWritten(
  events: LogEvent[],
  pathPattern: string | RegExp
): boolean {
  const written = filterByEvent(events, "file_written");
  if (typeof pathPattern === "string") {
    return written.some((e) => (e.path as string).includes(pathPattern));
  }
  return written.some((e) => pathPattern.test(e.path as string));
}

/**
 * Verify an agent_spawned event exists for the given agent name.
 */
export function expectAgentSpawned(
  events: LogEvent[],
  agentName: string
): boolean {
  return filterByEvent(events, "agent_spawned").some(
    (e) => e.agent === agentName
  );
}

/**
 * Verify a phase_completed event exists for the given phase.
 */
export function expectPhaseCompleted(
  events: LogEvent[],
  phaseName: string
): boolean {
  return filterByEvent(events, "phase_completed").some(
    (e) => e.phase === phaseName
  );
}

/**
 * Verify the build_result event matches expected outcome.
 */
export function expectBuildResult(
  events: LogEvent[],
  expected: "success" | "failure"
): boolean {
  const result = filterByEvent(events, "build_result")[0];
  if (!result) return false;
  return expected === "success" ? result.success === true : result.success === false;
}

/**
 * Verify specialist_pass_complete events are in the expected tier order
 * for a given recipe.
 */
export function expectSpecialistOrder(
  events: LogEvent[],
  recipe: string,
  expectedOrder: string[]
): boolean {
  const passes = filterByEvent(events, "specialist_pass_complete")
    .filter((e) => e.recipe_scope === recipe)
    .map((e) => e.specialist as string);

  // Filter expectedOrder to only specialists that actually ran
  const expected = expectedOrder.filter((s) => passes.includes(s));
  return JSON.stringify(passes) === JSON.stringify(expected);
}
```

- [ ] **Step 3: Commit**

```bash
git add tests/harness/lib/assertions.ts
git commit -m "Add skill-agnostic log assertions for unified test events"
git push
```

---

### Task 5: Extend fixtures with target repo/project helpers

**Files:**
- Modify: `tests/harness/lib/fixtures.ts`

- [ ] **Step 1: Add target path helpers**

Add these functions at the end of `tests/harness/lib/fixtures.ts`:

```typescript
/**
 * Get the target repo path for create-project-from-code tests.
 * Reads from TEST_TARGET_REPO env var, or falls back to a default.
 */
export function getTargetRepo(): string {
  const envPath = process.env.TEST_TARGET_REPO;
  if (envPath) return resolve(envPath);
  throw new Error(
    "TEST_TARGET_REPO env var must be set to a git repo path for create-project-from-code tests"
  );
}

/**
 * Get the target cookbook project path for generate/build tests.
 * Reads from TEST_TARGET_PROJECT env var, or falls back to a default.
 */
export function getTargetProject(): string {
  const envPath = process.env.TEST_TARGET_PROJECT;
  if (envPath) return resolve(envPath);
  throw new Error(
    "TEST_TARGET_PROJECT env var must be set to a cookbook project path for generate/build tests"
  );
}

/**
 * Create a test config file with the given overrides.
 * Returns the path to the created config file.
 */
export function createTestConfig(overrides: Record<string, string> = {}): string {
  const configDir = join(REPO_PATHS.testOutput, "config");
  if (!existsSync(configDir)) mkdirSync(configDir, { recursive: true });

  const configPath = join(configDir, `test-config-${Date.now()}.json`);
  const config = {
    interview_repo: REPO_PATHS.testOutput,
    cookbook_repo: REPO_PATHS.cookbook,
    interview_team_repo: REPO_PATHS.interviewTeam,
    user_name: "test-user",
    ...overrides,
  };

  writeFileSync(configPath, JSON.stringify(config, null, 2));
  return configPath;
}
```

- [ ] **Step 2: Commit**

```bash
git add tests/harness/lib/fixtures.ts
git commit -m "Add target repo/project helpers and dynamic config creation"
git push
```

---

### Task 6: Add test scripts to package.json

**Files:**
- Modify: `tests/harness/package.json`

- [ ] **Step 1: Add new test scripts**

Add these scripts to the `"scripts"` object in `tests/harness/package.json`:

```json
"test:create-project-from-code:smoke": "vitest run --config vitest.e2e.config.ts specs/create-project-from-code-smoke.test.ts",
"test:generate:smoke": "vitest run --config vitest.e2e.config.ts specs/generate-smoke.test.ts",
"test:build:smoke": "vitest run --config vitest.e2e.config.ts specs/build-smoke.test.ts",
"test:all:smoke": "vitest run --config vitest.e2e.config.ts specs/*-smoke.test.ts"
```

- [ ] **Step 2: Commit**

```bash
git add tests/harness/package.json
git commit -m "Add test scripts for create-project-from-code, generate, and build smoke tests"
git push
```

---

### Task 7: Add --test-mode to create-project-from-code skill

**Files:**
- Modify: `skills/create-project-from-code/SKILL.md`

- [ ] **Step 1: Add Test Mode section**

Add this section before the `## Error Handling` section at the end of `skills/create-project-from-code/SKILL.md`:

```markdown
## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract at `<interview_team_repo>/tests/test-mode-spec.md`.

Read the contract file at the start of test mode to understand the unified log schema.

### Test Mode Behavior

1. **Auto-approve all prompts.** Every `AskUserQuestion` call is auto-approved — proceed with the first/default option without waiting for input. This applies to:
   - Architecture scan confirmation ("Does this look right?")
   - Scope approval ("Want to add or remove any scopes?")
   - Overwrite confirmation ("A project already exists...")

2. **Write test log.** Append JSON events to `<output>/test-log.jsonl`:

   Phase boundaries:
   - `phase_started` / `phase_completed` for: `architecture-scan`, `scope-discovery`, `recipe-generation`, `project-assembly`, `summary`

   Agent interactions:
   - `agent_spawned` / `agent_completed` for: `codebase-scanner`, `scope-matcher`, `recipe-writer`, `project-assembler`

   Skill-specific events:
   - `architecture_scanned` — after scanner returns: `tech_stack`, `platforms`, `module_count`
   - `scopes_matched` — after matcher returns: `count`, `high_confidence`, `medium_confidence`, `low_confidence`
   - `recipe_generated` — after each recipe writer returns: `scope`, `output_path`, `needs_review_count`
   - `project_assembled` — after assembler returns: `component_count`, `manifest_path`

   File writes:
   - `file_written` for every artifact persisted: architecture-map.md, scope-report.md, each recipe, cookbook-project.json, generation-summary.md

   End:
   - `test_complete` summary

3. **Target path.** The `--target <path>` flag (or first positional arg) specifies the repo to create-project-from-code. In test mode, this is required.

4. **No profile updates.** Don't modify any user data.

5. **Config must pre-exist.** Fail immediately if config is missing.
```

- [ ] **Step 2: Add `--target` to the argument-hint in frontmatter**

Update the frontmatter `argument-hint` line to include `--target`:

```yaml
argument-hint: <repo-path> [--output <path>] [--config <path>] [--test-mode] [--target <path>]
```

- [ ] **Step 3: Commit**

```bash
git add skills/create-project-from-code/SKILL.md
git commit -m "Add --test-mode with unified logging to create-project-from-code skill"
git push
```

---

### Task 8: Write create-project-from-code smoke test

**Files:**
- Create: `tests/harness/specs/create-project-from-code-smoke.test.ts`

- [ ] **Step 1: Write the test spec**

```typescript
/**
 * Smoke test — analyze on a real repo.
 *
 * Verifies:
 * - Skill runs without errors
 * - Architecture map written
 * - Scope report written
 * - At least 1 recipe generated
 * - cookbook-project.json created
 * - Test log has expected events
 *
 * Requires: TEST_TARGET_REPO env var set to a git repo path.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { runSkill, type RunResult } from "../lib/runner.js";
import {
  getTargetRepo,
  createTestConfig,
  REPO_PATHS,
} from "../lib/fixtures.js";
import {
  fileExists,
  listFiles,
  expectFileWritten,
  expectAgentSpawned,
  expectPhaseCompleted,
} from "../lib/assertions.js";
import { parseLog, testSummary } from "../lib/log-parser.js";
import { existsSync, readdirSync, rmSync } from "fs";
import { join } from "path";

describe("create-project-from-code smoke test", () => {
  let result: RunResult;
  let outputDir: string;
  let configPath: string;
  let targetRepo: string;

  beforeAll(async () => {
    targetRepo = getTargetRepo();
    configPath = createTestConfig();

    // Derive expected output dir from repo name
    const repoName = targetRepo.split("/").pop()!;
    outputDir = join(REPO_PATHS.testOutput, "projects", `${repoName}-cookbook`);

    // Clean previous output
    if (existsSync(outputDir)) {
      rmSync(outputDir, { recursive: true, force: true });
    }

    console.log("[create-project-from-code-smoke] Starting analyze run...");
    console.log(`[create-project-from-code-smoke] target: ${targetRepo}`);
    console.log(`[create-project-from-code-smoke] output: ${outputDir}`);

    result = await runSkill({
      skillName: "create-project-from-code",
      cwd: targetRepo,
      configPath,
      targetPath: targetRepo,
      extraArgs: [`--output ${outputDir}`],
      timeout: 900_000, // 15 minutes
    });

    console.log(`[create-project-from-code-smoke] Completed. exitCode: ${result.exitCode}`);
  }, 960_000);

  it("completes without error", () => {
    expect([0, 143]).toContain(result.exitCode);
  });

  it("writes architecture-map.md", () => {
    expect(
      fileExists(outputDir, "context/research/architecture-map.md")
    ).toBe(true);
  });

  it("writes scope-report.md", () => {
    expect(
      fileExists(outputDir, "context/research/scope-report.md")
    ).toBe(true);
  });

  it("generates at least 1 recipe", () => {
    // Recipes live under app/ in the output dir
    const appDir = join(outputDir, "app");
    if (!existsSync(appDir)) {
      expect.fail("No app/ directory — no recipes generated");
    }
    // Recursively find .md files under app/
    function findMdFiles(dir: string): string[] {
      const results: string[] = [];
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (entry.isDirectory()) results.push(...findMdFiles(full));
        else if (entry.name.endsWith(".md")) results.push(full);
      }
      return results;
    }
    const recipes = findMdFiles(appDir);
    console.log(`[create-project-from-code-smoke] recipes found: ${recipes.length}`);
    expect(recipes.length).toBeGreaterThanOrEqual(1);
  });

  it("creates cookbook-project.json", () => {
    expect(fileExists(outputDir, "cookbook-project.json")).toBe(true);
  });

  it("writes test log with expected events", () => {
    const events = parseLog(outputDir);
    console.log(`[create-project-from-code-smoke] log events: ${events.length}`);

    expect(events.length).toBeGreaterThanOrEqual(1);
    expect(expectAgentSpawned(events, "codebase-scanner")).toBe(true);
    expect(expectAgentSpawned(events, "scope-matcher")).toBe(true);
    expect(expectAgentSpawned(events, "recipe-writer")).toBe(true);
    expect(expectAgentSpawned(events, "project-assembler")).toBe(true);
  });
});
```

Write this to `tests/harness/specs/create-project-from-code-smoke.test.ts`.

- [ ] **Step 2: Commit**

```bash
git add tests/harness/specs/create-project-from-code-smoke.test.ts
git commit -m "Add create-project-from-code smoke test spec"
git push
```

---

### Task 9: Add --test-mode to generate skill

**Files:**
- Modify: `skills/generate/SKILL.md`

- [ ] **Step 1: Add Test Mode section**

Add this section before the `## Aggressive Persistence` section in `skills/generate/SKILL.md`:

```markdown
## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract at `<interview_team_repo>/tests/test-mode-spec.md`.

Read the contract file at the start of test mode to understand the unified log schema.

### Test Mode Behavior

1. **Auto-approve all prompts.** Every `AskUserQuestion` call is auto-approved — proceed with the first/default option without waiting for input. This applies to:
   - Specialist assignment approval ("Want to adjust before I start reviews?")
   - Individual suggestion approval — **approve all suggestions**
   - Question answering — **skip all questions** (don't answer, mark as skipped)

2. **Write test log.** Append JSON events to `<project>/test-log.jsonl`:

   Phase boundaries:
   - `phase_started` / `phase_completed` for: `load-project`, `specialist-assignment`, `review-loop`, `final-report`

   Agent interactions:
   - `agent_spawned` / `agent_completed` for each `recipe-reviewer` instance

   Skill-specific events:
   - `reviewer_spawned` — when launching a reviewer: `recipe_scope`, `specialist`
   - `review_completed` — when a reviewer returns: `recipe_scope`, `specialist`, `suggestion_count`, `gap_count`
   - `suggestion_approved` — for each auto-approved suggestion: `recipe_scope`, `specialist`, `title`
   - `recipe_updated` — after applying changes to a recipe: `recipe_scope`, `changes_applied`, `new_version`

   File writes:
   - `file_written` for every artifact: review files, updated recipes, review-summary.md

   End:
   - `test_complete` summary

3. **Target path.** Use `--target <path>` or first positional arg for the cookbook project directory.

4. **No profile updates.** Don't modify any user data.

5. **Config must pre-exist.** Fail immediately if config is missing.
```

- [ ] **Step 2: Update frontmatter argument-hint**

```yaml
argument-hint: <project-path> [--specialist <domain>] [--recipe <scope>] [--config <path>] [--test-mode] [--target <path>]
```

- [ ] **Step 3: Commit**

```bash
git add skills/generate/SKILL.md
git commit -m "Add --test-mode with unified logging to generate skill"
git push
```

---

### Task 10: Write generate smoke test

**Files:**
- Create: `tests/harness/specs/generate-smoke.test.ts`

- [ ] **Step 1: Write the test spec**

```typescript
/**
 * Smoke test — generate on an existing cookbook project.
 *
 * Verifies:
 * - Skill runs without errors
 * - At least 1 recipe reviewed
 * - Review files written to context/reviews/
 * - At least 1 recipe version bumped
 * - Test log has expected events
 *
 * Requires: TEST_TARGET_PROJECT env var set to a cookbook project path.
 */

import { describe, it, expect, beforeAll } from "vitest";
import { runSkill, type RunResult } from "../lib/runner.js";
import { getTargetProject, createTestConfig } from "../lib/fixtures.js";
import {
  fileExists,
  listFiles,
  expectAgentSpawned,
  expectPhaseCompleted,
} from "../lib/assertions.js";
import { parseLog, filterByEvent, testSummary } from "../lib/log-parser.js";
import { existsSync } from "fs";
import { join } from "path";

describe("generate smoke test", () => {
  let result: RunResult;
  let projectDir: string;
  let configPath: string;

  beforeAll(async () => {
    projectDir = getTargetProject();
    configPath = createTestConfig();

    console.log("[generate-smoke] Starting generate run...");
    console.log(`[generate-smoke] project: ${projectDir}`);

    result = await runSkill({
      skillName: "generate",
      cwd: projectDir,
      configPath,
      targetPath: projectDir,
      timeout: 900_000,
    });

    console.log(`[generate-smoke] Completed. exitCode: ${result.exitCode}`);
  }, 960_000);

  it("completes without error", () => {
    expect([0, 143]).toContain(result.exitCode);
  });

  it("writes at least one review file", () => {
    const reviewsDir = join(projectDir, "context/reviews");
    if (!existsSync(reviewsDir)) {
      expect.fail("No context/reviews/ directory created");
    }
    const reviews = listFiles(projectDir, "context/reviews");
    console.log(`[generate-smoke] review files: ${reviews.length}`);
    expect(reviews.length).toBeGreaterThanOrEqual(1);
  });

  it("logs reviewer spawns", () => {
    const events = parseLog(projectDir);
    console.log(`[generate-smoke] log events: ${events.length}`);

    expect(expectAgentSpawned(events, "recipe-reviewer")).toBe(true);

    const reviewCompleted = filterByEvent(events, "review_completed");
    console.log(`[generate-smoke] reviews completed: ${reviewCompleted.length}`);
    expect(reviewCompleted.length).toBeGreaterThanOrEqual(1);
  });

  it("logs suggestion approvals (auto-approved in test mode)", () => {
    const events = parseLog(projectDir);
    const approved = filterByEvent(events, "suggestion_approved");
    console.log(`[generate-smoke] suggestions approved: ${approved.length}`);
    // In test mode, all suggestions are auto-approved
    // There should be at least 1 if any reviewer found issues
    // (it's possible a perfect recipe gets 0 suggestions — that's ok)
  });
});
```

Write this to `tests/harness/specs/generate-smoke.test.ts`.

- [ ] **Step 2: Commit**

```bash
git add tests/harness/specs/generate-smoke.test.ts
git commit -m "Add generate smoke test spec"
git push
```

---

### Task 11: Add --test-mode to build skill

**Files:**
- Modify: `skills/build/SKILL.md`

- [ ] **Step 1: Add Test Mode section**

Add this section before the `## Aggressive Persistence` section in `skills/build/SKILL.md`:

```markdown
## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract at `<interview_team_repo>/tests/test-mode-spec.md`.

Read the contract file at the start of test mode to understand the unified log schema.

### Test Mode Behavior

1. **Auto-approve all prompts.** Every `AskUserQuestion` call is auto-approved — proceed with the first/default option without waiting for input. This applies to:
   - Specialist assignment approval
   - Scaffold confirmation
   - Code review fix approval — **approve all fixes**
   - Build failure options — **choose "try more fixes" up to 2 extra attempts, then "skip to smoke tests"**
   - Resumability check — **choose "regenerate all"**

2. **Write test log.** Append JSON events to `<output>/test-log.jsonl`:

   Phase boundaries:
   - `phase_started` / `phase_completed` for: `load-project`, `specialist-assignment`, `scaffolding`, `code-generation`, `code-review`, `build`, `smoke-test`, `final-report`

   Agent interactions:
   - `agent_spawned` / `agent_completed` for: `project-scaffolder`, `code-generator`, `specialist-code-pass`, `build-runner`, `smoke-tester`

   Skill-specific events:
   - `scaffold_created` — after scaffolder returns: `build_system`, `file_count`, `build_command`
   - `code_generated` — after code-generator returns per recipe: `recipe_scope`, `files_written`, `must_implemented`, `must_total`
   - `specialist_pass_complete` — after each specialist pass: `recipe_scope`, `specialist`, `changes_count`
   - `code_review_complete` — after code review per recipe: `recipe_scope`, `issues_found`, `issues_fixed`
   - `build_attempted` — after each build attempt: `attempt`, `error_count`, `fixed_count`
   - `build_result` — final build outcome: `success`, `total_attempts`, `remaining_errors`
   - `smoke_test_result` — test results: `launch_pass`, `conformance_passed`, `conformance_failed`, `conformance_skipped`

   File writes:
   - `file_written` for every artifact: scaffold files, source code, generation logs, review reports, build report, test report, build summary

   End:
   - `test_complete` summary

3. **Target path.** Use `--target <path>` or first positional arg for the cookbook project directory.

4. **No profile updates.** Don't modify any user data.

5. **Config must pre-exist.** Fail immediately if config is missing.
```

- [ ] **Step 2: Update frontmatter argument-hint**

```yaml
argument-hint: <project-path> [--output <path>] [--recipe <scope>] [--platform <platform>] [--config <path>] [--test-mode] [--target <path>]
```

- [ ] **Step 3: Commit**

```bash
git add skills/build/SKILL.md
git commit -m "Add --test-mode with unified logging to build skill"
git push
```

---

### Task 12: Write build smoke test

**Files:**
- Create: `tests/harness/specs/build-smoke.test.ts`

- [ ] **Step 1: Write the test spec**

```typescript
/**
 * Smoke test — build on an existing cookbook project.
 *
 * Verifies:
 * - Skill runs without errors
 * - Project scaffold created
 * - At least 1 recipe's code generated
 * - Build attempted
 * - Smoke test attempted
 * - Test log has expected events
 *
 * Requires: TEST_TARGET_PROJECT env var set to a cookbook project path.
 */

import { describe, it, expect, beforeAll } from "vitest";
import { runSkill, type RunResult } from "../lib/runner.js";
import { getTargetProject, createTestConfig, REPO_PATHS } from "../lib/fixtures.js";
import {
  fileExists,
  expectAgentSpawned,
  expectPhaseCompleted,
  expectBuildResult,
} from "../lib/assertions.js";
import { parseLog, filterByEvent, testSummary } from "../lib/log-parser.js";
import { existsSync, readFileSync } from "fs";
import { join } from "path";

describe("build smoke test", () => {
  let result: RunResult;
  let projectDir: string;
  let outputDir: string;
  let configPath: string;

  beforeAll(async () => {
    projectDir = getTargetProject();
    configPath = createTestConfig();

    // Derive output dir — build creates <project>/../<name>-build/
    const projectName = projectDir.split("/").pop()!;
    const parentDir = join(projectDir, "..");
    outputDir = join(parentDir, `${projectName}-build`);

    console.log("[build-smoke] Starting build run...");
    console.log(`[build-smoke] project: ${projectDir}`);
    console.log(`[build-smoke] expected output: ${outputDir}`);

    result = await runSkill({
      skillName: "build",
      cwd: projectDir,
      configPath,
      targetPath: projectDir,
      extraArgs: [`--output ${outputDir}`],
      timeout: 1_800_000, // 30 minutes — builds are slow
    });

    console.log(`[build-smoke] Completed. exitCode: ${result.exitCode}`);
  }, 1_860_000); // 31 minutes

  it("completes without error", () => {
    expect([0, 143]).toContain(result.exitCode);
  });

  it("creates scaffold report", () => {
    expect(
      fileExists(outputDir, "context/build-log/scaffold-report.md")
    ).toBe(true);
  });

  it("spawns project-scaffolder agent", () => {
    const events = parseLog(outputDir);
    expect(expectAgentSpawned(events, "project-scaffolder")).toBe(true);
  });

  it("generates code for at least 1 recipe", () => {
    const events = parseLog(outputDir);
    const codeGenerated = filterByEvent(events, "code_generated");
    console.log(`[build-smoke] recipes with code: ${codeGenerated.length}`);
    expect(codeGenerated.length).toBeGreaterThanOrEqual(1);
  });

  it("runs specialist passes in tier order", () => {
    const events = parseLog(outputDir);
    const passes = filterByEvent(events, "specialist_pass_complete");
    console.log(
      `[build-smoke] specialist passes: ${passes.map((p) => `${p.recipe_scope}:${p.specialist}`).join(", ")}`
    );

    // Verify at least 1 specialist pass ran
    expect(passes.length).toBeGreaterThanOrEqual(1);

    // Verify tier ordering per recipe
    const TIER_ORDER = [
      "software-architecture",
      "reliability", "data-persistence", "networking-api",
      "security", "ui-ux-design", "accessibility", "localization-i18n",
      "testing-qa", "devops-observability", "code-quality", "development-process",
      "platform-ios-apple", "platform-android", "platform-windows",
      "platform-web-frontend", "platform-web-backend", "platform-database",
    ];

    // Group by recipe
    const byRecipe = new Map<string, string[]>();
    for (const p of passes) {
      const recipe = p.recipe_scope as string;
      if (!byRecipe.has(recipe)) byRecipe.set(recipe, []);
      byRecipe.get(recipe)!.push(p.specialist as string);
    }

    for (const [recipe, specialists] of byRecipe) {
      const expectedOrder = TIER_ORDER.filter((s) => specialists.includes(s));
      expect(specialists).toEqual(expectedOrder);
    }
  });

  it("attempts a build", () => {
    const events = parseLog(outputDir);
    const buildAttempts = filterByEvent(events, "build_attempted");
    console.log(`[build-smoke] build attempts: ${buildAttempts.length}`);
    expect(buildAttempts.length).toBeGreaterThanOrEqual(1);
  });

  it("writes build summary", () => {
    expect(
      fileExists(outputDir, "context/research/build-summary.md")
    ).toBe(true);
  });
});
```

Write this to `tests/harness/specs/build-smoke.test.ts`.

- [ ] **Step 2: Commit**

```bash
git add tests/harness/specs/build-smoke.test.ts
git commit -m "Add build smoke test spec"
git push
```

---

### Task 13: Migrate interview test-log to unified schema

**Files:**
- Modify: `skills/interview/SKILL.md`

- [ ] **Step 1: Update the Test Mode section's log format**

In `skills/interview/SKILL.md`, find the Test Mode section (around line 294). Update the flow logging description to use the unified schema. Replace the existing log format instructions:

Find the current log format block:
```markdown
2. **Flow logging.** Write a structured log to `<interview_repo>/projects/<project>/test-log.jsonl`. Each line is a JSON object:
   - `{"event": "specialist_invoked", "specialist": "<domain>", "mode": "structured|exploratory", "timestamp": "..."}`
   - `{"event": "question_asked", "specialist": "<domain>", "question": "<text>", "timestamp": "..."}`
   - `{"event": "answer_received", "transcript_file": "<filename>", "timestamp": "..."}`
   - `{"event": "analysis_written", "analysis_file": "<filename>", "transcript_id": "<id>", "timestamp": "..."}`
   - `{"event": "checklist_updated", "topic": "<topic>", "action": "covered|discovered", "timestamp": "..."}`
3. **Bounded execution.** Stop after `--max-exchanges` question-answer pairs. Write a final summary to the log: `{"event": "test_complete", "exchanges": N, "specialists_invoked": [...], "files_written": N, "timestamp": "..."}`.
```

Replace with:
```markdown
2. **Flow logging.** Follow the unified log schema defined in `<interview_team_repo>/tests/test-mode-spec.md`. Write events to `<interview_repo>/projects/<project>/test-log.jsonl`. Each line is a JSON object with base fields `skill`, `phase`, `event`, `timestamp`:
   - `{"skill": "interview", "phase": "interview-loop", "event": "specialist_invoked", "specialist": "<domain>", "mode": "structured|exploratory", "timestamp": "..."}`
   - `{"skill": "interview", "phase": "interview-loop", "event": "question_asked", "specialist": "<domain>", "question_id": "<id>", "timestamp": "..."}`
   - `{"skill": "interview", "phase": "interview-loop", "event": "answer_received", "transcript_file": "<filename>", "timestamp": "..."}`
   - `{"skill": "interview", "phase": "interview-loop", "event": "analysis_written", "analysis_file": "<filename>", "transcript_id": "<id>", "timestamp": "..."}`
   - `{"skill": "interview", "phase": "interview-loop", "event": "checklist_updated", "topic": "<topic>", "action": "covered|discovered", "timestamp": "..."}`
   - Also write `phase_started`/`phase_completed` for: `startup`, `interview-loop`, `summary`
   - Also write `agent_spawned`/`agent_completed` for: `transcript-analyzer`, `specialist-interviewer`, `specialist-analyst`, `simulated-user`
   - Also write `file_written` for: each transcript file, each analysis file, checklist updates
3. **Bounded execution.** Stop after `--max-exchanges` question-answer pairs. Write a final summary to the log: `{"skill": "interview", "phase": "summary", "event": "test_complete", "phases_completed": N, "agents_spawned": N, "files_written": N, "errors": 0, "timestamp": "..."}`.
```

- [ ] **Step 2: Commit**

```bash
git add skills/interview/SKILL.md
git commit -m "Migrate interview test-log to unified schema with skill/phase fields"
git push
```

---

### Task 14: Update existing interview test assertions for unified schema

**Files:**
- Modify: `tests/harness/lib/assertions.ts`

- [ ] **Step 1: Update the `TestLogEvent` interface**

The existing `TestLogEvent` interface (around line 91) needs `skill` and `phase` fields. Update it:

Find:
```typescript
export interface TestLogEvent {
  event: string;
  specialist?: string;
```

Replace with:
```typescript
export interface TestLogEvent {
  skill?: string;
  phase?: string;
  event: string;
  specialist?: string;
```

The `?` optionals preserve backward compatibility — legacy log events without these fields still parse.

- [ ] **Step 2: Verify existing interview tests still compile**

Run: `cd tests/harness && npx tsc --noEmit`

Expected: No type errors. The existing interview test specs (`smoke.test.ts`, etc.) use `TestLogEvent` through `parseTestLog` which returns the same shape plus optional new fields.

- [ ] **Step 3: Commit**

```bash
git add tests/harness/lib/assertions.ts
git commit -m "Add skill/phase fields to TestLogEvent for unified schema compatibility"
git push
```

---

### Task 15: Update vitest config for build test timeout

**Files:**
- Modify: `tests/harness/vitest.e2e.config.ts`

- [ ] **Step 1: Increase timeout for build tests**

The current 16-minute timeout is fine for interview/create-project-from-code/generate, but build tests need 30+ minutes. Update the config to use a longer timeout:

```typescript
import { defineConfig } from "vitest/config";

/** E2E config — skill tests that invoke Claude. */
export default defineConfig({
  test: {
    globals: true,
    include: ["specs/*.test.ts"],
    exclude: ["specs/unit/**"],
    testTimeout: 1_860_000, // 31 minutes — build tests are the longest
    hookTimeout: 1_860_000, // 31 minutes — beforeAll runs the skill
    reporters: ["verbose"],
    pool: "threads",
    poolOptions: {
      threads: { maxThreads: 1 }, // serialize — one skill run at a time
    },
  },
});
```

- [ ] **Step 2: Commit**

```bash
git add tests/harness/vitest.e2e.config.ts
git commit -m "Increase E2E test timeout to 31 minutes for build tests"
git push
```

---

## Verification

After all tasks are complete, verify the infrastructure works:

1. **Type check:** `cd tests/harness && npx tsc --noEmit` — should pass with no errors
2. **Run create-project-from-code smoke test:**
   ```bash
   cd tests/harness
   TEST_TARGET_REPO=~/projects/agentic-cookbook/agentic-cookbook npm run test:create-project-from-code:smoke
   ```
3. **Run generate smoke test** (requires a cookbook project from a prior analyze run):
   ```bash
   cd tests/harness
   TEST_TARGET_PROJECT=<path-to-cookbook-project> npm run test:generate:smoke
   ```
4. **Run build smoke test** (requires a cookbook project):
   ```bash
   cd tests/harness
   TEST_TARGET_PROJECT=<path-to-cookbook-project> npm run test:build:smoke
   ```
5. **Run existing interview smoke test** (verify no regression):
   ```bash
   cd tests/harness
   npm run test:smoke
   ```
