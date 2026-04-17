# Specialty-Team File Specification

Version: 1.0.0

Each specialty-team is a standalone markdown file that defines a worker-verifier pair focused on one source document.

## File Location

`specialty-teams/<category>/<name>.md` where:
- `<category>` matches a specialist filename in `specialists/`
- `<name>` is lowercase kebab-case, typically derived from the source document name

## Frontmatter

```yaml
---
name: <kebab-case-name>
description: <human-readable description of what this team covers>
artifact: <path to one source document, relative to sources base>
version: <semver>
---
```

| Field | Format | Description |
|-------|--------|-------------|
| name | `[a-z][a-z0-9]*(-[a-z0-9]+)*` | Unique within category, matches filename |
| description | Free text, ~120 chars | Human-readable summary for discovery |
| artifact | Path ending in `.md` | Single source document this team works from |
| version | `N.N.N` semver | Tracks changes to this team definition |

## Body Sections

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

| ID | Rule | Severity |
|----|------|----------|
| ST01 | File has valid YAML frontmatter with `---` delimiters | FAIL |
| ST02 | name field matches `[a-z][a-z0-9]*(-[a-z0-9]+)*` and matches filename | FAIL |
| ST03 | artifact field is non-empty and ends with `.md` | FAIL |
| ST04 | version field is valid semver (`N.N.N`) | FAIL |
| ST05 | Worker Focus section exists and is non-empty | WARN |
| ST06 | Verify section exists and is non-empty | WARN |
