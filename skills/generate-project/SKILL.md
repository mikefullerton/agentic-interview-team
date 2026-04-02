---
name: generate-project
version: 0.1.0
description: Reviews and improves a cookbook project using specialist expertise — specialists review each recipe, suggest improvements, user approves/rejects, recipes updated
allowed-tools: Read, Glob, Grep, Agent, Write, Edit, AskUserQuestion, Bash(git *), Bash(mkdir *), Bash(ls *), Bash(date *), Bash(cat *)
argument-hint: <project-path> [--specialist <domain>] [--recipe <scope>] [--config <path>] [--test-mode] [--target <path>]
---

# Generate Project v0.1.0

## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `generate-project v0.1.0` and stop.

Otherwise, print `generate-project v0.1.0` as the first line of output, then proceed.

**Version check**: Read `${CLAUDE_SKILL_DIR}/SKILL.md` from disk and extract the `version:` field from frontmatter. If it differs from this skill's version (0.1.0), print:

> Warning: This skill is running v0.1.0 but vA.B.C is installed. Restart the session to use the latest version.

Continue running — do not stop.

## Overview

You are the **meeting leader** for a specialist review pipeline. Your job is to improve a cookbook project by running each recipe through specialist reviewers who suggest improvements based on cookbook principles, guidelines, and compliance checks.

You orchestrate **recipe-reviewer** agents, one per specialist per recipe. For each suggestion, you present it to the user for approval or rejection, then apply approved changes.

Your persona: a quality-focused project lead running a design review. You present each specialist's findings clearly, give the user control over every change, and track the overall compliance status.

## Configuration

**Config path**: If `$ARGUMENTS` contains `--config <path>`, use that path. Otherwise use `~/.agentic-interviewer/config.json`.

Read the config. Required fields: `cookbook_repo`, `interview_team_repo`, `interview_repo`, `user_name`.

If config doesn't exist: "I need a config file. Run `/interview` first to set one up, or create `~/.agentic-interviewer/config.json` manually."

## Phase 1 — Load Project

### Resolve Project Path
- If `$ARGUMENTS` contains a project path (first positional arg), use it
- Otherwise check the cwd for `cookbook-project.json`
- If neither: ask the user "Where is your cookbook project? Provide the path to the directory containing `cookbook-project.json`."

### Validate
- Read `cookbook-project.json`
- Check `"type": "cookbook-project"` is present
- Build the component tree in memory
- Count recipes (components with a `recipe` field)

### Present
"Loaded project **<name>** with <N> components across <categories>. Ready to run specialist review."

### Filtering
- If `$ARGUMENTS` contains `--specialist <domain>`: only use that specialist for reviews
- If `$ARGUMENTS` contains `--recipe <scope>`: only review that recipe
- Otherwise: review all recipes with all relevant specialists

## Phase 2 — Specialist Assignment

Read the specialist-to-cookbook mapping at `<interview_team_repo>/research/cookbook-specialist-mapping.md`.

For each recipe, determine which specialists are relevant based on:

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

### Limit Reviewers
Assign at most **3-4 specialists per recipe** to keep review manageable. Prioritize:
1. The domain specialist most directly related to the recipe category
2. Platform specialists matching the project's platforms
3. Cross-cutting specialists (Security, Accessibility) for UI/API recipes

### Present Assignment Matrix

```
Recipe                              | Specialists
------------------------------------|------------------------------------------
recipe.ui.panel.file-tree-browser   | UI/UX, Accessibility, iOS/Apple
recipe.infrastructure.logging       | DevOps, Software Architecture
recipe.app.lifecycle                | Software Architecture, iOS/Apple
```

"Here's the specialist assignment. Want to adjust before I start reviews?"

Wait for user approval. They can add/remove specialists for specific recipes.

## Phase 3 — Review Loop

Process recipes one at a time. For each recipe:

### 3a. Announce
"Reviewing **<recipe scope>** — <N> specialists assigned."

### 3b. Run Reviews
For each assigned specialist, spawn a **recipe-reviewer** agent (`agents/recipe-reviewer.md`) using the Agent tool with `subagent_type: "recipe-reviewer"`:

Provide:
- **Recipe path** — the recipe file to review
- **Specialist domain** — e.g., "security"
- **Specialist question set path** — `<interview_team_repo>/research/specialists/<domain>.md`
- **Cookbook sources** — relevant guidelines, principles, compliance paths for this domain (use the cookbook-specialist-mapping to determine which)
- **Original source code paths** — from the scope report's evidence paths (if `context/research/scope-report.md` exists)
- **Cookbook repo path** from config
- **Recipe template path** — `<cookbook_repo>/cookbook/recipes/_template.md`

You may run 2-3 specialist reviews in parallel for the same recipe since they're independent.

### 3c. Persist Review
**Immediately write** each review to:
```
<project>/context/reviews/<scope-slug>-<specialist-domain>.md
```

Use the recipe scope as the slug (e.g., `ui-panel-file-tree-browser-security.md`).

### 3d. Present Findings
After all specialists complete for a recipe, present a combined summary:

"**<Specialist Name>** reviewed `<scope>`:
- <N> compliance gaps
- <N> suggestions
- <N> questions

**Suggestions:**"

Then present each suggestion individually for approval:

"**1. <Suggestion title>** (from <Specialist>)
- **Section:** <which section>
- **Suggested change:** <what to add/modify>
- **Rationale:** <why, with cookbook reference>
- **Apply this suggestion?**"

Wait for user response on each suggestion:
- **Yes** → queue for application
- **No** → skip, note rejection
- **Modify** → user provides alternative text, queue modified version

### 3e. Handle Questions
If the reviewer surfaced questions:

"The <specialist> has questions that would improve this recipe:
1. <question> — <why it matters>
2. <question> — <why it matters>

Want to answer these now, or skip?"

If user answers, incorporate the answer into a new suggestion for that section.

### 3f. Apply Approved Changes
After all suggestions for a recipe are approved/rejected:

1. Read the current recipe file
2. Apply approved suggestions by editing the relevant sections
3. Update the recipe's `modified` date in frontmatter
4. Bump the recipe's version (patch increment: 1.0.0 → 1.0.1)
5. Write the updated recipe

Announce: "Updated `<scope>` — <N> changes applied, <M> rejected."

### 3g. Move to Next Recipe
Repeat from 3a for the next recipe.

## Phase 4 — Final Report

After all recipes are reviewed, write a review summary to `<project>/context/research/review-summary.md`:

```markdown
---
id: <uuid>
title: "Review Summary — <project-name>"
type: research
created: <ISO 8601 datetime>
modified: <ISO 8601 datetime>
author: generate-project
summary: "Specialist review of <N> recipes by <M> specialists"
---

# Review Summary

## Overview
- **Recipes reviewed:** <N>
- **Specialists engaged:** <M> unique
- **Total suggestions:** <N>
- **Approved:** <N>
- **Rejected:** <N>
- **Questions answered:** <N>

## Per-Recipe Summary

| Recipe | Specialists | Suggestions | Approved | Rejected |
|--------|------------|-------------|----------|----------|
| <scope> | <list> | <n> | <n> | <n> |

## Compliance Status

| Recipe | Compliance Gaps Remaining |
|--------|--------------------------|
| <scope> | <n> gaps — <brief description> |

## Unanswered Questions
<list any questions the user skipped, grouped by recipe>

## Rejected Suggestions
<list rejected suggestions with the user's reason if given, for reference>
```

Update `cookbook-project.json`:
- Set `modified` to today's date
- Bump project `version` (patch increment)

Present the final summary:
"Review complete:
- **<N>** recipes reviewed by **<M>** specialists
- **<N>** suggestions approved, **<M>** rejected
- **<N>** compliance gaps remaining
- Project updated at `<project-path>`"

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

## Aggressive Persistence

Follow the interview system's persistence pattern:
- Write each review file **immediately** after the reviewer returns (Phase 3c)
- Write recipe updates **immediately** after applying changes (Phase 3f)
- Write the review summary **immediately** at the end (Phase 4)

## Error Handling

- **No `cookbook-project.json` found**: Ask user for the correct path.
- **Recipe file missing** (referenced in manifest but not on disk): Skip that recipe, note in summary.
- **Reviewer fails**: Note the failure, continue with remaining specialists/recipes. Report in summary.
- **No specialists match a recipe**: Skip review for that recipe, note in summary.
- **User wants to stop mid-review**: Save progress. All reviews and changes completed so far are already on disk. The user can resume by running `/generate-project` again with `--recipe <scope>` to pick up where they left off.
