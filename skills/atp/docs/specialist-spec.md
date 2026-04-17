# Specialist File Specification

Version: 1.0.0

The formal specification for specialist definition files. Machine-referenceable contract for any team built on the team-pipeline.

## File Location

`specialists/<domain>.md` where `<domain>` is lowercase kebab-case (e.g., `security`, `temperament`).

## Required Sections

Sections MUST appear in this order. No other `##` headings may appear between them except where noted.

### 1. Title

```markdown
# <Name> Specialist
```

- Exactly one `#` heading
- MUST end with ` Specialist`
- `<Name>` is the human-readable specialist name (title case, spaces allowed)

### 2. Role

```markdown
## Role
<prose>
```

- 1-3 sentences defining the specialist's domain scope
- Plain prose, no markdown lists or sub-headings
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

The persona shapes how the specialist communicates across all modes. It is NOT the specialist's domain knowledge (that's the Role and Specialty Teams) — it's the specialist's *character*.

**Sub-sections:**

| Sub-section | Required | Description |
|-------------|----------|-------------|
| Archetype | YES | One sentence defining the expert's identity |
| Voice | YES | Communication style — tone, register, rhythm. 2-4 sentences. |
| Priorities | YES | What this specialist optimizes for when trade-offs arise. 2-4 sentences. |
| Anti-Patterns | NO | What this specialist never does. Table or list format. |

**Placeholder**: `(coming)` is acceptable as a transitional state but SHOULD be replaced.

### 4. Sources

```markdown
## Sources
- <description or path to reference material>
```

- Markdown list describing what knowledge/reference material this specialist draws from
- Can be backtick-wrapped paths, descriptions, or both
- Directory references MAY include a file count: `(N files)`

### 5. Manifest

```markdown
## Manifest
- specialty-teams/<category>/<team-name>.md
- specialty-teams/<category>/<team-name>.md
```

- Markdown list of paths to specialty-team files, relative to the team's plugin root
- Each path MUST resolve to an existing file in `specialty-teams/`
- At least one entry required
- See `specialty-team-spec.md` for the file format

### 5b. Consulting Teams (optional)

```markdown
## Consulting Teams
- consulting-teams/<category>/<team-name>.md
```

- Markdown list of paths to consulting-team files
- Each path MUST resolve to an existing file in `consulting-teams/`
- See `consulting-team-spec.md` for the file format

### 6. Exploratory Prompts (optional)

```markdown
## Exploratory Prompts

1. <question>?
2. <question>?
```

- Numbered list of domain-specific questions for interview mode's exploratory phase
- Each prompt SHOULD end with `?`

## Validation Rules

### Structure (S-series)

| ID | Rule | Severity |
|----|------|----------|
| S01 | Title matches `# <Name> Specialist` pattern | FAIL |
| S02 | All required sections present in correct order: Role, Persona, Sources, Manifest | FAIL |
| S03 | Each manifest path resolves to a file with valid frontmatter and body sections | FAIL |
| S04 | name field in each referenced team file matches `[a-z][a-z0-9]*(-[a-z0-9]+)*` and matches filename | FAIL |
| S05 | artifact field in each referenced team file is non-empty and ends with `.md` | FAIL |
| S06 | Worker Focus and Verify sections in each referenced team file are non-empty | WARN |

### Content (C-series)

| ID | Rule | Severity |
|----|------|----------|
| C01 | Manifest has at least one entry | FAIL |
| C02 | Exploratory Prompts (if present) are numbered and end with `?` | WARN |
| C03 | Role section is non-empty | FAIL |
| C04 | Persona is not `(coming)` placeholder | WARN |
| C05 | Persona has required sub-sections (Archetype, Voice, Priorities) when not placeholder | FAIL |

## Parser Contract

`scripts/run_specialty_teams.py` reads specialist files and outputs a JSON object with `specialty_teams` and `consulting_teams` arrays. It relies on:

- `## Manifest` heading to enter manifest reading
- `- ` prefixed lines to collect team file paths
- Next `## ` heading or EOF to exit manifest reading
- For each referenced file: YAML frontmatter for `name` and `artifact`, `## Worker Focus` and `## Verify` body sections
- `## Consulting Teams` heading (if present) for consulting-team paths
