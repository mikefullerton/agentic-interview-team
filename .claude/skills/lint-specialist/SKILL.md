---
name: lint-specialist
version: "1.0.0"
description: "Validate specialist files against the specialist spec. Use when creating, editing, or reviewing specialist definitions."
argument-hint: "[<path>] [--all] [--fix]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(ls *), Bash(wc *)
context: fork
---

# Lint Specialist

Validate specialist definition files against the formal spec at `docs/specialist-spec.md`.

## Startup

If `$ARGUMENTS` is `--version`, respond with `lint-specialist v1.0.0` and STOP.

## Step 1 — Resolve Targets

- If `$ARGUMENTS` contains a file path, use that as the single target
- If `$ARGUMENTS` contains `--all`, glob `specialists/*.md` and exclude any file named `specialist-guide.md`
- If `$ARGUMENTS` is empty, ask: "Which specialist to lint? Provide a path or use `--all` for all specialists."

Check if `--fix` flag is present — if so, offer to auto-fix simple issues after the report.

## Step 2 — Load References

Read the validation checklist at `${CLAUDE_SKILL_DIR}/references/specialist-checks.md`. This defines checks S01-S07 (structure) and C01-C06 (content).

Try to load the cookbook repo path from `~/.agentic-cookbook/dev-team/config.json` (field: `cookbook_repo`). If unavailable, note that checks C01 (directory expansion), C03 (artifact existence) will be skipped.

## Step 3 — Lint Each Target

For each specialist file, read the full contents and run every check:

### Structure Checks

- **S01**: First line matches `# <Name> Specialist`
- **S02**: Extract all `## ` headings. Verify `## Role`, `## Persona`, `## Cookbook Sources`, `## Specialty Teams` all exist and appear in that order. Other `## ` headings (like `## Conventions`, `## Exploratory Prompts`) may appear after `## Specialty Teams`.
- **S03**: For each `### ` heading inside `## Specialty Teams`, check that the subsequent lines (before the next `### ` or `## `) contain all 3 field prefixes: `- **Artifact**:`, `- **Worker focus**:`, `- **Verify**:`
- **S04**: Each team name (text after `### `) matches `[a-z][a-z0-9]*(-[a-z0-9]+)*`
- **S05**: Each `- **Artifact**:` line contains backtick-wrapped content (`` ` `` pairs)
- **S06**: Check the line following each `- **Worker focus**:` and `- **Verify**:` line — if it doesn't start with `- **`, `### `, or `## `, the field value spans multiple lines
- **S07**: Extract text after `- **Worker focus**: ` and `- **Verify**: ` — check for `"` characters

### Content Checks

- **C01**: Parse all paths from `## Cookbook Sources` (text between backticks on list item lines). For each:
  - If it ends with `/` (directory reference) and cookbook_repo is available: list files in that directory, check each has a team with matching artifact
  - If it's a specific file: check there's a team with that exact artifact path
- **C02**: For each team's artifact path, verify it (or its parent directory with trailing `/`) appears in Cookbook Sources
- **C03**: If cookbook_repo is available, check `<cookbook_repo>/<artifact_path>` exists on disk
- **C04**: Count `### ` headings inside `## Specialty Teams` — must be >= 1
- **C05**: If `## Exploratory Prompts` exists, check each numbered item ends with `?`
- **C06**: Text between `## Role` and the next `## ` heading is non-empty after trimming

## Step 4 — Report

For each specialist, print a structured report:

```
Linting specialists/<domain>.md...
PASS  S01  Title: "# <Name> Specialist"
PASS  S02  Required sections present and ordered
FAIL  S03  Team "foo" missing Verify field
PASS  S04  Team names: all kebab-case
WARN  C03  Artifact "guidelines/example/old.md" not found in cookbook

Result: 1 FAIL, 1 WARN, 11 PASS
```

Order: FAILs first, then WARNs, then PASSes.

After all specialists, print a summary:

```
Summary: <N> specialists linted
  <N> PASS  <N> WARN  <N> FAIL
```

## Step 5 — Fix (if --fix)

If `--fix` was specified and there are fixable issues:

- **S04** (non-kebab team names): Offer to rename
- **S05** (missing backticks): Offer to wrap artifact paths
- **S07** (double quotes): Offer to replace `"` with single quotes
- **S03** (missing fields): Offer to add stub fields (`- **Verify**: TODO`)

For each fix, show the change and ask for confirmation before applying.

Do NOT attempt to fix C01/C02/C03 automatically — those require understanding the cookbook structure.

## Usage

```
/lint-specialist specialists/security.md
/lint-specialist --all
/lint-specialist specialists/new-domain.md --fix
```
