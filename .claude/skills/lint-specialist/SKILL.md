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
- **S02**: Extract all `## ` headings. Verify `## Role`, `## Persona`, `## Cookbook Sources`, `## Manifest` all exist and appear in that order. Other `## ` headings (like `## Conventions`, `## Exploratory Prompts`) may appear after `## Manifest`.
- **S03**: For each `- ` line in `## Manifest`, resolve the path to a file. Check it has valid YAML frontmatter with fields: `name`, `description`, `artifact`, `version`. Check it has body sections `## Worker Focus` and `## Verify`.
- **S04**: Check the `name` field in each referenced team file matches `[a-z][a-z0-9]*(-[a-z0-9]+)*` and matches the filename (without `.md`).
- **S05**: Check the `artifact` field in each referenced team file is non-empty and ends with `.md`.
- **S06**: Check `## Worker Focus` and `## Verify` sections in each referenced team file are non-empty (have content after the heading).

### Content Checks

- **C01**: Parse all paths from `## Cookbook Sources` (text between backticks on list item lines). For each, resolve through manifest team files' artifact fields to verify coverage:
  - If it ends with `/` (directory reference) and cookbook_repo is available: list files in that directory, check each has a team in the manifest whose artifact matches
  - If it's a specific file: check there's a manifest team whose artifact matches
- **C02**: For each manifest team's artifact (from the team file's frontmatter), verify it (or its parent directory with trailing `/`) appears in Cookbook Sources
- **C03**: If cookbook_repo is available, check `<cookbook_repo>/<artifact_path>` exists on disk for each manifest team's artifact
- **C04**: Count `- ` lines inside `## Manifest` — must be >= 1
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

- **S04** (non-kebab team names): Offer to rename the team file and update its `name` field
- **S05** (missing/invalid artifact): Offer to fix the artifact path in team file frontmatter
- **S03** (missing fields/sections): Offer to add stub frontmatter fields or body sections

For each fix, show the change and ask for confirmation before applying.

Do NOT attempt to fix C01/C02/C03 automatically — those require understanding the cookbook structure.

## Usage

```
/lint-specialist specialists/security.md
/lint-specialist --all
/lint-specialist specialists/new-domain.md --fix
```
