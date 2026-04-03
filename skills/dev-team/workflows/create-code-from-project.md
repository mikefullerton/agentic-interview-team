<!-- Workflow: create-code-from-project — loaded by /dev-team router -->

# Build Project

## Overview

You are the **meeting leader** for a project build pipeline. Your job is to take a cookbook project (recipes describing components behaviorally) and produce a working, buildable codebase.

You orchestrate a team of agents:
1. **Project scaffolder** — creates the native build system skeleton
2. **Code generator** — generates base implementation from each recipe
3. **Specialist code pass** — each specialist augments code with their domain concerns (sequential)
4. **Build runner** — compiles the project, fixes errors iteratively
5. **Smoke tester** — verifies the app launches and runs conformance tests

Your persona: a build lead turning specifications into working software. You present progress at each stage, persist every artifact immediately, and proceed based on the execution mode.

## Execution Mode

The router passes the execution mode: **one-shot** or **incremental**.

- **One-shot**: Run all phases without pausing for approval. Present brief status after each phase but proceed immediately. Still stop on errors, output directory conflicts, and build failures that exhaust retries.
- **Incremental**: Pause between phases for user review and approval as described in each phase below. Sections marked "(incremental only)" are skipped in one-shot mode.

## UI Framework Selection (Apple platforms)

If `$ARGUMENTS` contains `--no-swiftui`:
- **macOS**: Use AppKit (NSWindow, NSView, NSViewController, storyboards or programmatic)
- **iOS**: Use UIKit (UIWindow, UIView, UIViewController, storyboards or programmatic)
- Do NOT use SwiftUI for any UI code

If `--no-swiftui` is NOT present (default):
- Use SwiftUI for all UI code on Apple platforms
- This is the default because SwiftUI is the modern standard

Pass this preference to the **code-generator** and **specialist-code-pass** agents as part of their input context, so they know which UI framework to target.

## DB Integration

At workflow start:
- `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-project.sh --name <project-name> --path <project-path>`
- `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-run.sh start --project $PROJECT_ID --workflow create-code-from-project`

Pass `$PROJECT_ID` and `$RUN_ID` to all spawned agents. Log agents with `db-agent.sh`, build logs with `db-artifact.sh` (categories: `build-log`, `report`), activity with `db-message.sh`.

At end: `db-run.sh complete --id $RUN_ID --status completed`

### Resumability

At workflow start, check for an interrupted run:
```
${CLAUDE_PLUGIN_ROOT}/scripts/db/db-run.sh --latest --project $PROJECT_ID --workflow create-code-from-project
```
If the latest run has `status: interrupted`, query its agent_runs to determine which phases and specialist passes completed. Skip completed work and resume.

### Specialist Tracking

After specialist assignment is approved, log each assignment:
```
${CLAUDE_PLUGIN_ROOT}/scripts/db/db-query.sh "INSERT INTO specialist_assignments (project_id, workflow_run_id, recipe_path, specialist, tier, approved) VALUES ($PROJECT_ID, $RUN_ID, '<recipe>', '<specialist>', <tier>, 1)"
```

## Phase 1 — Load Project

### Resolve Project Path
- If `$ARGUMENTS` contains a project path (first positional arg), use it
- Otherwise check the cwd for `cookbook-project.json`
- If neither: ask "Where is your cookbook project? Provide the path to the directory containing `cookbook-project.json`."

### Validate
- Read `cookbook-project.json`
- Check `"type": "cookbook-project"` is present
- Build the component tree in memory
- Count recipes (components with a `recipe` field)
- Extract the `platforms` array — this determines build system and platform specialists
- Read `context/research/architecture-map.md` if it exists — for tech stack details

### Present
"Loaded project **<name>** with <N> recipes targeting **<platforms>**. Ready to build."

### Filtering
- If `$ARGUMENTS` contains `--recipe <scope>`: only build that recipe
- If `$ARGUMENTS` contains `--platform <platform>`: only build for that platform
- Otherwise: build all recipes for all platforms

### Resumability Check
If the output directory already exists with generated code, ask: "I see code already exists for <N> recipes. Regenerate all, only missing/failed ones, or pick a new output directory?"

## Phase 2 — Specialist Assignment & Ordering

Read the specialist assignment rules at `${CLAUDE_PLUGIN_ROOT}/research/specialist-assignment.md`.

For each recipe, determine and order specialists by tier:

```
${CLAUDE_PLUGIN_ROOT}/scripts/assign-specialists.sh <recipe-path> --platforms '<platforms-json>' --tier-order
```

The `--tier-order` flag sorts specialists by build tier (foundation -> core -> cross-cutting -> platform).

Limit to 3-4 specialists per recipe. Present the assignment matrix with execution order.

### Present Assignment Matrix

```
Recipe                              | Specialist Passes (in order)
------------------------------------|----------------------------------------------
recipe.ui.panel.file-tree-browser   | software-architecture → ui-ux-design → accessibility → platform-ios-apple
recipe.infrastructure.logging       | software-architecture → devops-observability
recipe.app.lifecycle                | software-architecture → reliability → platform-ios-apple
```

**(Incremental only):** "Here's the specialist assignment and ordering. Want to adjust before I start building?" Wait for user approval. They can add/remove specialists or change ordering for specific recipes.

**(One-shot):** Proceed to Phase 3 immediately.

## Phase 3 — Project Scaffolding

### Determine Output Directory
- If `$ARGUMENTS` contains `--output <path>`, use that
- Otherwise: `<project-path>/../<project-name>-build/`
- If the output directory already exists and user hasn't chosen to regenerate: ask "A build already exists at `<path>`. Overwrite, or pick a new path?"

### Detect Build System
Determine from platforms and architecture map:

| Platform(s) | Build System | Build Command | Test Command |
|-------------|-------------|---------------|--------------|
| `ios`, `macos` | SwiftPM | `swift build` | `swift test` |
| `android` | Gradle | `./gradlew assembleDebug` | `./gradlew test` |
| `web` (frontend) | npm/Vite | `npm run build` | `npm test` |
| `web` (backend) | npm | `npm run build` | `npm test` |
| `windows` | .NET | `dotnet build` | `dotnet test` |
| `rust` | Cargo | `cargo build` | `cargo test` |

If the architecture map specifies a framework or build system, use that instead of the default.

### Scaffold

Tell the user: "Scaffolding **<build-system>** project at `<output-path>`..."

Spawn the **project-scaffolder** agent (`agents/project-scaffolder.md`) using the Agent tool with `subagent_type: "project-scaffolder"`:

Provide:
- **Output directory** path
- **`cookbook-project.json` path**
- **Platforms** array
- **Project name**
- **Architecture map path** (if available)
- **Cookbook repo path** from config

**Immediately persist** the scaffold report to:
```
<output>/context/build-log/scaffold-report.md
```

Present: "Created **<build-system>** project at `<output-path>`. Build command: `<command>`."

**(Incremental only):** Wait for user confirmation before proceeding to code generation.

**(One-shot):** Proceed to Phase 4 immediately.

## Phase 4 — Code Generation Loop

### Dependency Ordering

Before generating code, topologically sort recipes by their `depends-on` fields from the component tree. Dependencies must be generated first so dependent components can reference their interfaces.

If there are circular dependencies, warn the user and proceed with an arbitrary ordering.

### Determine Target Language

From platform:
- `ios`/`macos` → Swift — UI Framework: SwiftUI (default) or AppKit/UIKit (if `--no-swiftui`)
- `android` → Kotlin
- `web` (frontend) → TypeScript
- `web` (backend) → TypeScript (default) or Python/Go if architecture map specifies
- `windows` → C#
- `rust` → Rust

### Process Recipes

For each recipe (in dependency order):

#### 4a. Announce
"Building **<recipe scope>** — 1 code generator + <N> specialist passes."

#### 4b. Generate Base Code

Spawn the **code-generator** agent (`agents/code-generator.md`) using the Agent tool with `subagent_type: "code-generator"`:

Provide:
- **Recipe path**
- **Target platform** and **language**
- **Output source file path(s)** — derive from recipe scope and scaffold structure
- **Scaffold report path** — so the generator knows project structure
- **Architecture map path** (if available)
- **Cookbook repo path** from config
- **Dependent recipe paths** — recipes this component depends on
- **UI framework preference** — "SwiftUI" or "AppKit" (macOS) / "UIKit" (iOS) based on `--no-swiftui` flag (Apple platforms only)

**Immediately persist** the generated code.

Brief status: "✓ Base code generated for `<scope>`"

#### 4c. Sequential Specialist Passes

For each assigned specialist (in tier order), spawn a **specialist-code-pass** agent (`agents/specialist-code-pass.md`) using the Agent tool with `subagent_type: "specialist-code-pass"`:

Provide:
- **Source file path(s)** — the code files just generated (or augmented by previous pass)
- **Recipe path**
- **Specialist domain**
- **Specialist question set path** — `${CLAUDE_PLUGIN_ROOT}/specialists/<domain>.md`
- **Cookbook guidelines paths** — relevant guidelines for this domain (use cookbook-specialist-mapping)
- **Target platform and language**
- **UI framework preference** — "SwiftUI" or "AppKit" (macOS) / "UIKit" (iOS) based on `--no-swiftui` flag (Apple platforms only)
- **Previous specialist passes** — list of which specialists have already run

**Important**: Run specialist passes **sequentially**, not in parallel. Each pass reads the output of the previous one.

**Immediately persist** after each pass.

Brief status after each: "✓ <specialist> pass complete for `<scope>`"

#### 4d. Persist Generation Log

Write a per-recipe generation log to:
```
<output>/context/build-log/<scope-slug>-generation.md
```

Include the code-generator report and each specialist's augmentation report.

#### 4e. Parallelization of Independent Recipes

Recipes that don't depend on each other can be processed in parallel (2-3 at a time). But within each recipe, the specialist passes are sequential.

Group independent recipes and process them concurrently. When a recipe depends on another, wait for the dependency to complete first.

#### 4f. After All Recipes

Summarize: "Generated code for **<N>** recipes. **<M>** specialist passes applied total."

## Phase 5 — Code Review

Tell the user: "Reviewing generated code against recipes..."

For each recipe, spawn a code review using the Agent tool (general-purpose agent):

Provide in the prompt:
- The generated source file path(s) for this recipe
- The recipe path
- Instructions to review the code against the recipe: Does the code implement all MUST requirements? Are there bugs, missing edge cases, or inconsistencies?
- The scaffold report (for project context)

You may run 2-3 code reviews in parallel since they're independent.

**Immediately persist** each review to:
```
<output>/context/reviews/<scope-slug>-code-review.md
```

### Present Findings

After all reviews complete, present a combined summary per recipe:

"Code review for `<scope>`:
- <N> issues found
- <N> MUST requirements verified implemented
- <N> potential bugs flagged"

For critical issues (missing MUST requirements, likely bugs), present individually:

"**Issue: <title>**
- **File:** `<path>:<line>`
- **Problem:** <description>
- **Suggested fix:** <what to change>
- **Apply this fix?**"

**(Incremental only):** Wait for user response. Apply approved fixes, persist immediately.

**(One-shot):** Auto-apply all suggested fixes for critical issues (missing MUST requirements, likely bugs). Skip non-critical suggestions.

After all reviews: "Code review complete. **<N>** issues found, **<M>** fixed."

## Phase 6 — Build

Tell the user: "Building the project..."

Spawn the **build-runner** agent (`agents/build-runner.md`) using the Agent tool with `subagent_type: "build-runner"`:

Provide:
- **Project root path** — the output directory
- **Build command** — from scaffold report
- **Platform and language**
- **Maximum retry attempts** — 5

**Immediately persist** the build report to:
```
<output>/context/build-log/build-report.md
```

### Handle Results

**Build succeeds:**
"Build succeeded on attempt <N>. <M> errors fixed during compilation."

**Build fails after max retries:**
Present remaining errors:

"Build failed with <N> remaining errors after <M> attempts:
1. `<file>:<line>` — `<error>`
2. `<file>:<line>` — `<error>`

Options:
1. **Try more fixes** — I'll attempt to fix these manually
2. **Skip to smoke tests** — test what we have
3. **Stop here** — you'll fix the remaining errors"

**(Incremental only):** Wait for user choice.

**(One-shot):** Try more fixes (up to 2 extra attempts), then skip to smoke tests if still failing.

If user chooses "try more fixes," attempt direct fixes yourself (read the file, understand the error, edit the fix), then re-run the build command.

## Phase 7 — Smoke Test

Tell the user: "Running smoke tests..."

Spawn the **smoke-tester** agent (`agents/smoke-tester.md`) using the Agent tool with `subagent_type: "smoke-tester"`:

Provide:
- **Project root path**
- **Platform and language**
- **Recipe paths** — all recipe file paths
- **Test framework** — XCTest/JUnit/Jest/Vitest/cargo test based on platform
- **Run command** — from scaffold report
- **Build command** — from scaffold report (for rebuilding with tests)

**Immediately persist** the test report to:
```
<output>/context/research/test-report.md
```

Present results:

"Smoke test results:
- **Launch test:** <pass/fail/skipped>
- **Conformance tests:** <X> passed, <Y> failed, <Z> skipped (out of <N> total)

<if failures>
Failed tests:
- `<test-id>` (<recipe scope>): <brief description>
- ..."

## Final Report

Write a build summary to `<output>/context/research/build-summary.md`:

```markdown
---
id: <uuid>
title: "Build Summary — <project-name>"
type: research
created: <ISO 8601 datetime>
modified: <ISO 8601 datetime>
author: build
summary: "Built <project-name> from <N> recipes with <M> specialist passes"
---

# Build Summary

## Project
- **Name:** <project-name>
- **Platforms:** <platforms>
- **Build System:** <detected system>
- **Output:** <output-path>

## Code Generation
- **Recipes built:** <N>
- **Specialist passes:** <M> total across <K> unique specialists
- **MUST requirements implemented:** <N> of <M>
- **Code review issues found:** <N> (fixed: <M>)

## Build
- **Result:** <success/failure>
- **Attempts:** <N>
- **Errors fixed during build:** <M>
- **Errors remaining:** <K>

## Smoke Tests
- **Launch test:** <pass/fail/skipped>
- **Conformance tests:** <passed>/<total> (<percentage>%)
- **Failed tests:** <list if any>

## Files Generated
<count of source files, test files, config files>

## Component Tree
<paste the component tree showing which recipes were built>

## Next Steps
<suggestions based on results — e.g., fix failing tests, address remaining build errors, add missing requirements>
```

## Build Transcript

Query the DB for all messages from this run and write the full transcript:

```
${CLAUDE_PLUGIN_ROOT}/scripts/db/db-query.sh "SELECT timestamp, agent_type, specialist_domain, message FROM messages WHERE workflow_run_id=$RUN_ID ORDER BY timestamp"
```

Write to `<output>/context/build-log/build-transcript.md`:

```markdown
---
title: "Build Transcript — <project-name>"
type: transcript
created: <ISO 8601 datetime>
author: create-code-from-project
workflow_run_id: <RUN_ID>
---

# Build Transcript

## Run Info
- **Project:** <project-name>
- **Platforms:** <platforms>
- **Build System:** <build-system>
- **Specialists:** <list of specialists assigned>
- **Started:** <timestamp>
- **Completed:** <timestamp>

## Transcript

| Time | Agent | Specialist | Message |
|------|-------|------------|---------|
| <for each message row from the DB query, one table row> |

## Summary
- **Recipes built:** <N>
- **Specialist passes:** <M> total
- **MUST requirements implemented:** <N> of <M>
- **Code review issues:** <N> found, <M> fixed
- **Build result:** <success/failure> in <N> attempts
- **Tests:** <passed>/<total>
- **Findings:** <N> FAIL, <M> WARN
```

Also log the transcript file as an artifact: `db-artifact.sh write --project $PROJECT_ID --run $RUN_ID --path <file> --category transcript`

Copy `cookbook-project.json` into the output directory (if not already there), annotating it with build metadata:
- Add `"build"` section with date, version, result, test results

Present the final summary:
"Build complete:
- **<N>** recipes built with **<M>** specialist passes
- **Build:** <succeeded/failed>
- **Tests:** <X>/<Y> passing (<percentage>%)
- **Output at:** `<output-path>`"

## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract in `${CLAUDE_PLUGIN_ROOT}/tests/test-mode-spec.md`.

## Aggressive Persistence

Follow the interview system's persistence pattern:
- Write the scaffold report **immediately** after the scaffolder returns (Phase 3)
- Write each source file **immediately** after code generation and each specialist pass (Phase 4)
- Write each generation log **immediately** after all passes for a recipe complete (Phase 4d)
- Write each code review **immediately** after the reviewer returns (Phase 5)
- Write the build report **immediately** after the build runner returns (Phase 6)
- Write the test report **immediately** after the smoke tester returns (Phase 7)
- Write the build summary **immediately** at the end

If the session is interrupted at any point, everything up to the last completed step is on disk.

## Error Handling

- **No `cookbook-project.json` found**: Ask user for the correct path.
- **Empty component tree**: "This project has no recipes. Run `/dev-team create-project-from-code` first."
- **Scaffolder fails**: Report the error and stop. Can't generate code without a project skeleton.
- **Code generator fails for a recipe**: Skip that recipe, note in summary, continue with others.
- **Specialist pass fails**: Log which specialist failed for which recipe, continue with next specialist. Code from the previous pass is still on disk.
- **Build fails after max retries**: Present errors, offer options (see Phase 6).
- **Smoke tests fail**: Report failures. Do NOT attempt to fix code to match tests.
- **Build toolchain not installed**: Detect on first attempt (e.g., `swift: command not found`). Tell user what to install.
- **Unsupported platform**: "Platform <X> isn't supported yet. Supported: ios, macos, android, web, windows, rust." Skip that platform.
- **User wants to stop mid-build**: Save progress. All code and reports completed so far are on disk. User can resume with `--recipe <scope>`.
