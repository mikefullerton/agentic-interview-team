# Specialist File Specification

Version: 1.0.0

The formal specification for specialist definition files in `specialists/`. This is the machine-referenceable contract — for architecture context and usage guidance, see `specialist-guide.md`.

## File Location

`specialists/<domain>.md` where `<domain>` is lowercase kebab-case (e.g., `security`, `platform-ios-apple`).

## Required Sections

Sections MUST appear in this order. No other `##` headings may appear between them except where noted.

### 1. Title

```markdown
# <Name> Specialist
```

- Exactly one `#` heading
- MUST end with ` Specialist`
- `<Name>` is the human-readable specialist name (title case, spaces allowed)
- Examples: `# Security Specialist`, `# iOS / Apple Platforms Specialist`

### 2. Role

```markdown
## Role
<prose>
```

- 1-3 sentences defining the specialist's domain scope
- Plain prose, no markdown lists or sub-headings
- Comma-separated keywords are the conventional style
- MUST be non-empty

### 3. Persona

```markdown
## Persona

### Archetype
<1 sentence — what kind of expert this is>

### Voice
<how this specialist communicates — tone, directness, register>

### Priorities
<what this specialist cares most about when forced to choose>

### Anti-Patterns
<what this specialist never does>
```

The persona shapes how the specialist communicates across all modes (interview questions, code review findings, recipe suggestions). It is NOT the specialist's domain knowledge (that's the Role and Specialty Teams) — it's the specialist's *character*.

**Sub-sections:**

| Sub-section | Required | Description |
|-------------|----------|-------------|
| Archetype | YES | One sentence defining the expert's identity (e.g., "Security auditor who's investigated real breaches and knows what attackers actually exploit") |
| Voice | YES | Communication style — tone (direct/measured), register (technical/plain), rhythm (terse/detailed). 2-4 sentences. |
| Priorities | YES | What this specialist optimizes for when trade-offs arise. What it escalates vs. what it lets slide. 2-4 sentences. |
| Anti-Patterns | NO | What this specialist never does. Table format with "What" and "Why" columns, or a short list. |

**Placeholder**: `(coming)` is acceptable as a transitional state but SHOULD be replaced with a full persona definition. The `/lint-specialist` tool will flag `(coming)` as a WARN.

**Design reference**: Persona structure inspired by the character-driven persona model (archetype, voice, priorities, anti-patterns) — see `docs/research/persona-design.md` for background.

### 4. Cookbook Sources

```markdown
## Cookbook Sources
- `<path>`
- `<path>` (<N> files)
```

- Markdown list of backtick-wrapped paths relative to the cookbook repo root
- Directory references MAY include a file count: `(N files)`
- Sub-headings (`### Guidelines`, `### Principles`, etc.) are allowed for organization
- Each path MUST be either a file or directory that exists in the cookbook repo
- Every path listed here MUST have corresponding specialty-team(s)

### 5. Manifest

```markdown
## Manifest
- specialty-teams/<category>/<team-name>.md
- specialty-teams/<category>/<team-name>.md
```

- Markdown list of paths to specialty-team files, relative to the repo root
- Each path MUST resolve to an existing file in `specialty-teams/`
- At least one entry required
- See **Specialty-Team File Specification** below for the file format

### 6. Exploratory Prompts (optional)

```markdown
## Exploratory Prompts

1. <question>?
2. <question>?
```

- Numbered list of domain-specific questions
- Each prompt SHOULD end with `?`
- Used for interview mode's exploratory phase

## Optional Sections

These MAY appear between Manifest and Exploratory Prompts:

### Conventions

```markdown
## Conventions
<prose>
```

- Domain-specific naming, formatting, or structural rules
- Free-form prose

## Specialty-Team File Specification

Each specialty-team is a standalone markdown file in `specialty-teams/<category>/<name>.md`.

### File Location

`specialty-teams/<category>/<name>.md` where:
- `<category>` matches a specialist filename in `specialists/` (e.g., `security`, `platform-ios-apple`)
- `<name>` is lowercase kebab-case, typically derived from the artifact filename

### Frontmatter

```yaml
---
name: <kebab-case-name>
description: <human-readable description of what this team covers>
artifact: <path to one cookbook artifact, relative to cookbook root>
version: <semver>
---
```

| Field | Format | Description |
|-------|--------|-------------|
| name | `[a-z][a-z0-9]*(-[a-z0-9]+)*` | Unique within category, matches filename |
| description | Free text, ~120 chars | Human-readable summary for discovery |
| artifact | Cookbook-relative path ending in `.md` | Single file path (not a directory) |
| version | `N.N.N` semver | Tracks changes to this team definition |

### Body Sections

```markdown
## Worker Focus
<text>

## Verify
<text>
```

| Section | Description |
|---------|-------------|
| Worker Focus | What this team cares about (mode-independent). Guides the worker agent. |
| Verify | Concrete acceptance criteria. The verifier uses this to determine PASS/FAIL. |

## Validation Rules

### Structure (S-series)

| ID | Rule | Severity |
|----|------|----------|
| S01 | Title matches `# <Name> Specialist` pattern | FAIL |
| S02 | All required sections present in correct order: Role, Persona, Cookbook Sources, Manifest | FAIL |
| S03 | Each manifest path resolves to a file with valid frontmatter (name, description, artifact, version) and body sections (Worker Focus, Verify) | FAIL |
| S04 | name field in each referenced team file matches `[a-z][a-z0-9]*(-[a-z0-9]+)*` and matches filename | FAIL |
| S05 | artifact field in each referenced team file is non-empty and ends with `.md` | FAIL |
| S06 | Worker Focus and Verify sections in each referenced team file are non-empty | WARN |

### Content (C-series)

| ID | Rule | Severity |
|----|------|----------|
| C01 | Every file path in Cookbook Sources has a corresponding team in the manifest (resolve through team files' artifact fields) | FAIL |
| C02 | Every manifest team's artifact appears in Cookbook Sources (or its parent directory) | WARN |
| C03 | Artifact paths in team files resolve to real files in the cookbook repo | WARN |
| C04 | Manifest has at least one entry | FAIL |
| C05 | Exploratory Prompts (if present) are numbered and end with `?` | WARN |
| C06 | Role section is non-empty | FAIL |
| C07 | Persona is not `(coming)` placeholder | WARN |
| C08 | Persona has required sub-sections (Archetype, Voice, Priorities) when not placeholder | FAIL |

## Parser Contract

`scripts/run-specialty-teams.sh` reads specialist files and outputs a JSON array. It relies on:

- `## Manifest` heading to enter manifest reading
- `- ` prefixed lines to collect team file paths
- Next `## ` heading or EOF to exit manifest reading
- For each referenced file: YAML frontmatter for `name` and `artifact`, `## Worker Focus` and `## Verify` body sections for content
- Outputs one JSON object per team with fields: name, artifact, worker_focus, verify

## Example

```markdown
# Example Specialist

## Role
Example domain coverage description.

## Persona

### Archetype
Widget systems engineer who has shipped component libraries used by thousands of developers and knows where abstractions leak.

### Voice
Technical and specific. Prefers concrete measurements over qualitative assessments. Speaks in terms of constraints and invariants, not opinions. Short sentences. Will quote the spec before offering interpretation.

### Priorities
Correctness over aesthetics — a widget that works at every size beats one that looks perfect at one. Platform consistency over custom design. Accessibility is non-negotiable, not a nice-to-have. When time is short, cuts visual polish before cutting interaction quality.

### Anti-Patterns
| What | Why |
|------|-----|
| Never says "looks fine" without testing at extremes | Visual inspection misses edge cases that real devices expose |
| Never approves fixed pixel dimensions | They break on every device except the one used for testing |
| Never treats accessibility as a follow-up task | Retrofitting accessibility is 5x harder than building it in |

## Cookbook Sources
- `guidelines/example/`

## Manifest
- specialty-teams/example/widget-design.md
- specialty-teams/example/widget-accessibility.md

## Exploratory Prompts

1. If a user couldn't see your widgets, could they still use them?
2. What happens to your widget layout on the smallest supported screen?
```
