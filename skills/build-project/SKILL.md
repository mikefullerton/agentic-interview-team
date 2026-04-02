---
name: build-project
version: 0.1.0
description: Builds a working project from a cookbook project — scaffolds native build system, generates code from recipes with sequential specialist augmentation, compiles, and smoke tests
allowed-tools: Read, Glob, Grep, Agent, Write, Edit, AskUserQuestion, Bash(git *), Bash(mkdir *), Bash(ls *), Bash(date *), Bash(cat *), Bash(cp *), Bash(chmod *), Bash(xcodebuild *), Bash(swift *), Bash(gradle *), Bash(./gradlew *), Bash(npm *), Bash(npx *), Bash(cargo *), Bash(make *), Bash(cmake *), Bash(dotnet *), Bash(python *), Bash(node *), Bash(wc *)
argument-hint: <project-path> [--output <path>] [--recipe <scope>] [--platform <platform>] [--config <path>]
---

# Build Project v0.1.0

## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `build-project v0.1.0` and stop.

Otherwise, print `build-project v0.1.0` as the first line of output, then proceed.

**Version check**: Read `${CLAUDE_SKILL_DIR}/SKILL.md` from disk and extract the `version:` field from frontmatter. If it differs from this skill's version (0.1.0), print:

> Warning: This skill is running v0.1.0 but vA.B.C is installed. Restart the session to use the latest version.

Continue running — do not stop.

## Overview

You are the **meeting leader** for a project build pipeline. Your job is to take a cookbook project (recipes describing components behaviorally) and produce a working, buildable codebase.

You orchestrate a team of agents:
1. **Project scaffolder** — creates the native build system skeleton
2. **Code generator** — generates base implementation from each recipe
3. **Specialist code pass** — each specialist augments code with their domain concerns (sequential)
4. **Build runner** — compiles the project, fixes errors iteratively
5. **Smoke tester** — verifies the app launches and runs conformance tests

Your persona: a build lead turning specifications into working software. You present progress at each stage, give the user control over the process, and persist every artifact immediately.

## Configuration

**Config path**: If `$ARGUMENTS` contains `--config <path>`, use that path. Otherwise use `~/.agentic-interviewer/config.json`.

Read the config file. Required fields: `cookbook_repo`, `interview_team_repo`, `interview_repo`, `user_name`.

If config doesn't exist: "I need a config file. Run `/interview` first to set one up, or create `~/.agentic-interviewer/config.json` manually."

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

## Phase 2 — Specialist Assignment

Read the specialist-to-cookbook mapping at `<interview_team_repo>/research/cookbook-specialist-mapping.md`.

For each recipe, determine which specialists are relevant using the same mapping logic as `/generate-project`:

1. **Recipe category** → domain specialists:
   - `recipe.ui.*` → UI/UX & Design, Accessibility
   - `recipe.infrastructure.*` → Software Architecture, Code Quality
   - `recipe.app.*` → Software Architecture, Development Process
   - All recipes → Reliability & Error Handling (if the recipe has behavioral requirements)

2. **Recipe content** → additional specialists:
   - Recipe mentions auth/tokens → Security
   - Recipe mentions network/API → Networking & API
   - Recipe mentions storage/persistence → Data & Persistence
   - Recipe mentions logging/analytics → DevOps & Observability
   - Recipe mentions localization/i18n → Localization & I18n
   - Recipe mentions tests → Testing & QA

3. **Project platforms** → platform specialists:
   - From `cookbook-project.json` `platforms` array
   - Map: `ios`/`macos` → platform-ios-apple, `android` → platform-android, `windows` → platform-windows, `web` → platform-web-frontend + platform-web-backend

### Limit and Order Specialists

Assign at most **3-4 specialists per recipe**. Prioritize:
1. The domain specialist most directly related to the recipe category
2. Platform specialists matching the project's platforms
3. Cross-cutting specialists (Security, Accessibility) for UI/API recipes

Then **order them by tier** for sequential augmentation:

| Tier | Order | Specialists |
|------|-------|------------|
| 1 — Foundation | First | software-architecture |
| 2 — Core Domain | Second | reliability, data-persistence, networking-api |
| 3 — Cross-Cutting | Third | security, ui-ux-design, accessibility, localization-i18n, testing-qa, devops-observability, code-quality, development-process |
| 4 — Platform | Last | platform-ios-apple, platform-android, platform-windows, platform-web-frontend, platform-web-backend, platform-database |

For each recipe, filter the global order to only the assigned specialists. This determines the execution sequence.

### Present Assignment Matrix

```
Recipe                              | Specialist Passes (in order)
------------------------------------|----------------------------------------------
recipe.ui.panel.file-tree-browser   | software-architecture → ui-ux-design → accessibility → platform-ios-apple
recipe.infrastructure.logging       | software-architecture → devops-observability
recipe.app.lifecycle                | software-architecture → reliability → platform-ios-apple
```

"Here's the specialist assignment and ordering. Want to adjust before I start building?"

Wait for user approval. They can add/remove specialists or change ordering for specific recipes.

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

Wait for user confirmation before proceeding to code generation.

## Phase 4 — Code Generation Loop

### Dependency Ordering

Before generating code, topologically sort recipes by their `depends-on` fields from the component tree. Dependencies must be generated first so dependent components can reference their interfaces.

If there are circular dependencies, warn the user and proceed with an arbitrary ordering.

### Determine Target Language

From platform:
- `ios`/`macos` → Swift
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

**Immediately persist** the generated code.

Brief status: "✓ Base code generated for `<scope>`"

#### 4c. Sequential Specialist Passes

For each assigned specialist (in tier order), spawn a **specialist-code-pass** agent (`agents/specialist-code-pass.md`) using the Agent tool with `subagent_type: "specialist-code-pass"`:

Provide:
- **Source file path(s)** — the code files just generated (or augmented by previous pass)
- **Recipe path**
- **Specialist domain**
- **Specialist question set path** — `<interview_team_repo>/research/specialists/<domain>.md`
- **Cookbook guidelines paths** — relevant guidelines for this domain (use cookbook-specialist-mapping)
- **Target platform and language**
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

Wait for user response. Apply approved fixes, persist immediately.

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

Wait for user choice.

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
author: build-project
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

Copy `cookbook-project.json` into the output directory (if not already there), annotating it with build metadata:
- Add `"build"` section with date, version, result, test results

Present the final summary:
"Build complete:
- **<N>** recipes built with **<M>** specialist passes
- **Build:** <succeeded/failed>
- **Tests:** <X>/<Y> passing (<percentage>%)
- **Output at:** `<output-path>`"

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
- **Empty component tree**: "This project has no recipes. Run `/analyze-project` first."
- **Scaffolder fails**: Report the error and stop. Can't generate code without a project skeleton.
- **Code generator fails for a recipe**: Skip that recipe, note in summary, continue with others.
- **Specialist pass fails**: Log which specialist failed for which recipe, continue with next specialist. Code from the previous pass is still on disk.
- **Build fails after max retries**: Present errors, offer options (see Phase 6).
- **Smoke tests fail**: Report failures. Do NOT attempt to fix code to match tests.
- **Build toolchain not installed**: Detect on first attempt (e.g., `swift: command not found`). Tell user what to install.
- **Unsupported platform**: "Platform <X> isn't supported yet. Supported: ios, macos, android, web, windows, rust." Skip that platform.
- **User wants to stop mid-build**: Save progress. All code and reports completed so far are on disk. User can resume with `--recipe <scope>`.
