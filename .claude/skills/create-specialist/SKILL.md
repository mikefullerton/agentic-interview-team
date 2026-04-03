---
name: create-specialist
version: "1.0.0"
description: "Scaffold a new specialist definition from cookbook sources. Use when adding a new specialist domain."
argument-hint: "<name> [--from <existing-specialist>]"
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion, Bash(ls *), Bash(wc *)
---

# Create Specialist

Scaffold a new specialist file that conforms to `docs/specialist-spec.md`.

## Startup

If `$ARGUMENTS` is `--version`, respond with `create-specialist v1.0.0` and STOP.

## Step 1 — Parse Arguments

Extract from `$ARGUMENTS`:
- **name** (required, first positional arg): the specialist domain name in kebab-case (e.g., `infrastructure`, `ai-ml`)
- **--from <existing>** (optional): path to an existing specialist to use as a structural template

If no name provided, ask: "What's the specialist domain name? (kebab-case, e.g., `infrastructure`)"

Check if `specialists/<name>.md` already exists. If so, stop: "Specialist `<name>` already exists at `specialists/<name>.md`."

## Step 2 — Gather Domain Info

If `--from` was provided, read that specialist file to understand the structure and use it as a template.

Ask the user:

**Question 1**: "What does this specialist cover? (This becomes the Role — 1-3 sentences describing scope)"

**Question 2**: "Which cookbook sources does this specialist own? Provide file paths or directory paths relative to the cookbook root (e.g., `guidelines/infrastructure/`, `principles/scalability.md`, `compliance/infrastructure.md`)"

Try to load `cookbook_repo` from `~/.agentic-cookbook/dev-team/config.json` to resolve paths.

## Step 3 — Resolve Cookbook Sources

For each cookbook source path the user provided:
- If it's a directory: list all `.md` files in it (using the cookbook_repo path)
- If it's a file: verify it exists

Build the complete list of artifact files that need specialty-teams.

## Step 4 — Generate Specialty Teams

For each artifact file:

1. Read the cookbook artifact from `<cookbook_repo>/<path>`
2. Extract the key requirements, rules, and constraints from the artifact
3. Derive:
   - **Team name**: from the filename (e.g., `authentication.md` → `authentication`)
   - **Artifact**: the path as provided
   - **Worker focus**: synthesize the artifact's core concerns into a single line
   - **Verify**: synthesize concrete acceptance criteria from the artifact's requirements

Present the draft teams to the user for review before writing.

## Step 5 — Write the Specialist File

Write to `specialists/<name>.md` using this structure:

```markdown
# <Title Case Name> Specialist

## Role
<user's role description>

## Persona
(coming)

## Cookbook Sources
<list of paths from Step 2>

## Specialty Teams

### <team-name>
- **Artifact**: `<path>`
- **Worker focus**: <derived from artifact>
- **Verify**: <derived from artifact>

...

## Exploratory Prompts

1. <generated domain question>?
2. <generated domain question>?
3. <generated domain question>?
```

Generate 3-5 exploratory prompts based on the domain — these should be thought-provoking questions about trade-offs, blind spots, and edge cases in the specialist's domain.

## Step 6 — Validate

Run the lint checks from `docs/specialist-spec.md` against the generated file:
- S01-S07 structure checks
- C01-C06 content checks (if cookbook_repo is available)

Report any issues. Fix them before finalizing.

## Step 7 — Summary

Print:
```
Created specialists/<name>.md
  Role: <role summary>
  Teams: <N> specialty-teams
  Artifacts: <N> cookbook artifacts covered
  
Run /lint-specialist specialists/<name>.md to validate.
```

## Usage

```
/create-specialist ai-ml
/create-specialist infrastructure --from specialists/devops-observability.md
```
