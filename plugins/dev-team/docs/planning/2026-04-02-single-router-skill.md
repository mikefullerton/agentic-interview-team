# Consolidate Plugin to Single Router Skill

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate 6 separate skills into a single `/dev-team` skill with subcommands, reducing context cost and improving UX.

**Architecture:** One thin router skill (`skills/dev-team/SKILL.md`) parses the subcommand from `$ARGUMENTS`, then loads the appropriate workflow file from `skills/dev-team/workflows/`. Each workflow file contains the full skill logic (moved from the old SKILL.md). Shared startup (version check, config loading) happens once in the router.

**Tech Stack:** Markdown skills, `$ARGUMENTS` parsing, `${CLAUDE_SKILL_DIR}` references.

---

## Context

The plugin currently has 6 skills, each with its own description loaded into every session (~1200 chars of always-on context). Consolidating to one skill with subcommands:
- Reduces context to ~200 chars (one description)
- Provides clearer UX: `/dev-team interview` instead of `/dev-team interview`
- Centralizes shared logic (version check, config) in the router instead of duplicating in each workflow
- Aligns with progressive disclosure: only the invoked workflow loads

## Current → New Command Mapping

| Current Command | New Command | Subcommand |
|----------------|-------------|------------|
| `/dev-team interview` | `/dev-team interview` | `interview` |
| `/dev-team create-project-from-code` | `/dev-team create-project-from-code` | `create-project-from-code` |
| `/dev-team generate` | `/dev-team generate` | `generate` |
| `/dev-team build` | `/dev-team build` | `build` |
| `/dev-team lint` | `/dev-team lint` | `lint` |
| `/dev-team view-project` | `/dev-team view-project` | `view-project` |

## New Directory Structure

```
skills/
  dev-team/
    SKILL.md                              # Router (~40 lines)
    workflows/
      interview.md                        # Full interview workflow (moved from skills/interview/SKILL.md)
      create-project-from-code.md         # Full analysis workflow
      generate.md                         # Full generate workflow
      build.md                            # Full build workflow
      lint.md                             # Full lint workflow
      view-project.md                     # Full view workflow
```

---

## Task 1: Create the router skill and move workflows

**Files:**
- Create: `skills/dev-team/SKILL.md`
- Create: `skills/dev-team/workflows/` (directory)
- Move: `skills/interview/SKILL.md` → `skills/dev-team/workflows/interview.md`
- Move: `skills/create-project-from-code/SKILL.md` → `skills/dev-team/workflows/create-project-from-code.md`
- Move: `skills/generate/SKILL.md` → `skills/dev-team/workflows/generate.md`
- Move: `skills/build/SKILL.md` → `skills/dev-team/workflows/build.md`
- Move: `skills/lint/SKILL.md` → `skills/dev-team/workflows/lint.md`
- Move: `skills/view-project/SKILL.md` → `skills/dev-team/workflows/view-project.md`
- Remove: old skill directories (`skills/interview/`, `skills/create-project-from-code/`, `skills/generate/`, `skills/build/`, `skills/lint/`, `skills/view-project/`)

- [ ] **Step 1:** Create the router skill at `skills/dev-team/SKILL.md`:

```markdown
---
name: dev-team
version: 0.2.0
description: Multi-agent dev team for product discovery, project creation, specialist review, building, and linting. Subcommands: interview, create-project-from-code, generate, build, lint, view-project.
allowed-tools: Read, Glob, Grep, Agent, Write, Edit, AskUserQuestion, Bash(git *), Bash(mkdir *), Bash(ls *), Bash(date *), Bash(cat *), Bash(wc *), Bash(uuidgen), Bash(chmod *), Bash(open *), WebFetch
argument-hint: <command> [args...] — commands: interview, create-project-from-code, generate, build, lint, view-project
---

# Dev Team v0.2.0

## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `dev-team v0.2.0` and stop.

Otherwise, print `dev-team v0.2.0` as the first line of output.

**Version check**: Run `${CLAUDE_PLUGIN_ROOT}/scripts/version-check.sh "${CLAUDE_SKILL_DIR}" "0.2.0"`. If it outputs a warning, print it and continue.

## Configuration

**Config path**: If `$ARGUMENTS` contains `--config <path>`, use that path.

Run: `${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh` with `--config <path>` if specified. If the script fails (exit code 1), the error message tells the user what's wrong.

Extract `cookbook_repo`, `workspace_repo`, and `user_name` from the JSON output.

If config doesn't exist and the subcommand is NOT `interview`: "I need a config file. Run `/dev-team interview` first to set one up, or create `~/.agentic-cookbook/dev-team/config.json` manually."

## Routing

Parse the first positional argument from `$ARGUMENTS` as the subcommand. Everything after it becomes the subcommand's arguments.

| Subcommand | Workflow File |
|------------|--------------|
| `interview` | `${CLAUDE_SKILL_DIR}/workflows/interview.md` |
| `create-project-from-code` | `${CLAUDE_SKILL_DIR}/workflows/create-project-from-code.md` |
| `generate` | `${CLAUDE_SKILL_DIR}/workflows/generate.md` |
| `build` | `${CLAUDE_SKILL_DIR}/workflows/build.md` |
| `lint` | `${CLAUDE_SKILL_DIR}/workflows/lint.md` |
| `view-project` | `${CLAUDE_SKILL_DIR}/workflows/view-project.md` |

Read the workflow file and follow its instructions. Pass the remaining arguments as the workflow's input.

If no subcommand is provided or the subcommand is `help`, print:

```
Dev Team v0.2.0 — Multi-agent product development

Commands:
  interview                    Product discovery interview
  create-project-from-code     Reverse-engineer codebase into cookbook project
  generate                     Specialist review of cookbook project recipes
  build                        Build working code from cookbook project
  lint                         Evaluate artifacts against cookbook standards
  view-project                 View cookbook project in browser

Usage: /dev-team <command> [args...]
```

If the subcommand is unrecognized, print the help text above and say "Unknown command: `<subcommand>`".
```

- [ ] **Step 2:** Create `skills/dev-team/workflows/` directory

- [ ] **Step 3:** Move each skill's content to a workflow file. For each:
  - Read the old SKILL.md
  - Strip the YAML frontmatter (the router handles that now)
  - Strip the Startup section (version check and config loading are in the router)
  - Strip the Configuration section (handled by the router)
  - Keep everything else (Overview, Phases, Test Mode reference, Error Handling)
  - Write to `skills/dev-team/workflows/<name>.md`

  Files to move:
  - `skills/interview/SKILL.md` → `skills/dev-team/workflows/interview.md`
    - **Special:** Keep the interview's config CREATION logic (first-time setup) since the router only loads config, doesn't create it. Add a note: "If config was not loaded by the router (first invocation), create it interactively as described below."
  - `skills/create-project-from-code/SKILL.md` → `skills/dev-team/workflows/create-project-from-code.md`
  - `skills/generate/SKILL.md` → `skills/dev-team/workflows/generate.md`
  - `skills/build/SKILL.md` → `skills/dev-team/workflows/build.md`
  - `skills/lint/SKILL.md` → `skills/dev-team/workflows/lint.md`
  - `skills/view-project/SKILL.md` → `skills/dev-team/workflows/view-project.md`

- [ ] **Step 4:** Remove old skill directories:
  ```bash
  git rm -r skills/interview skills/create-project-from-code skills/generate skills/build skills/lint skills/view-project
  ```

- [ ] **Step 5:** Commit and push

---

## Task 2: Update all internal references

**Files:**
- Modify: `.claude/CLAUDE.md`
- Modify: `agents/*.md` (any that reference old skill commands)
- Modify: `research/specialists/specialist-guide.md`
- Modify: `planning/*.md`
- Modify: `tests/test-mode-spec.md`
- Modify: `tests/harness/**` (test fixtures, specs)

- [ ] **Step 1:** Update `.claude/CLAUDE.md`:
  - Skills table: replace 6 rows with single `/dev-team` entry, then list subcommands
  - Repository Structure: replace 6 skill directories with single `dev-team/` containing `workflows/`

New Skills section:
```markdown
## Skills

Single entry point: `/dev-team <command>`

| Command | Role | Responsibility |
|---------|------|---------------|
| `interview` | Interviewer | Discover product requirements through structured and exploratory questioning with specialist expertise |
| `create-project-from-code` | Project Creator | Reverse-engineer a codebase into a cookbook project |
| `generate` | Project Generator | Improve a cookbook project through specialist review |
| `build` | Project Builder | Build working code from a cookbook project |
| `lint` | Linter | Evaluate any artifact against cookbook standards |
| `view-project` | Viewer | Generate HTML view of a cookbook project |
```

New Repository Structure:
```
skills/
  dev-team/                # Single skill with subcommand routing
    SKILL.md               # Router
    workflows/             # One workflow file per subcommand
```

- [ ] **Step 2:** Grep the entire repo for old command patterns and update:
  - `/dev-team interview` → `/dev-team interview`
  - `/dev-team create-project-from-code` → `/dev-team create-project-from-code`
  - `/dev-team generate` → `/dev-team generate`
  - `/dev-team build` → `/dev-team build`
  - `/dev-team lint` → `/dev-team lint`
  - `/dev-team view-project` → `/dev-team view-project`
  - `/dev-team interview` → `dev-team interview` (plugin:skill namespace syntax may appear)
  - Same for all other `dev-team:*` patterns

- [ ] **Step 3:** Update `tests/test-mode-spec.md` — skill names in examples and per-skill tables

- [ ] **Step 4:** Update test harness files if they reference old skill names

- [ ] **Step 5:** Commit and push

---

## Task 3: Update plugin manifest

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1:** Read `.claude-plugin/plugin.json`
- [ ] **Step 2:** If it lists skills explicitly, update to reflect the single `dev-team` skill
- [ ] **Step 3:** Bump plugin version to 0.2.0 to match the skill
- [ ] **Step 4:** Commit and push

---

## Verification

1. **Help text:** Run `/dev-team` with no arguments — should print help with all 6 subcommands
2. **Version:** Run `/dev-team --version` — should print `dev-team v0.2.0`
3. **Unknown command:** Run `/dev-team foo` — should print help and "Unknown command: foo"
4. **Each subcommand loads:** Run `/dev-team interview`, `/dev-team lint <path>`, etc. — each should load its workflow and start executing
5. **No old references:** `grep -r "dev-team-interview\|dev-team-create-project-from-code\|dev-team-generate\|dev-team-build\|dev-team-lint\|dev-team-view-project" --include="*.md"` — should find nothing
6. **Config shared:** Verify config loading happens in the router, not re-done in workflow files
