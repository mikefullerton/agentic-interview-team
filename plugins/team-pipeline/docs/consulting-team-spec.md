# Consulting-Team File Specification

Version: 1.0.0

Each consulting-team is a standalone markdown file that defines a consulting worker-verifier pair focused on one cross-cutting concern.

## File Location

`consulting-teams/<category>/<name>.md` where:
- `<category>` matches a specialist filename in `specialists/`
- `<name>` is lowercase kebab-case

## Frontmatter

```yaml
---
name: <kebab-case-name>
description: <human-readable description of what this consultant checks>
type: consulting
source:
  - <path to research doc>
  - <path to research doc>
version: <semver>
---
```

| Field | Format | Description |
|-------|--------|-------------|
| name | `[a-z][a-z0-9]*(-[a-z0-9]+)*` | Unique within category, matches filename |
| description | Free text, ~120 chars | Human-readable summary for discovery |
| type | `consulting` | Must be exactly `consulting` |
| source | YAML list of paths | Research documents this consultant draws from |
| version | `N.N.N` semver | Tracks changes to this consulting-team definition |

## Body Sections

```markdown
## Consulting Focus
<text>

## Verify
<text>
```

| Section | Description |
|---------|-------------|
| Consulting Focus | What cross-cutting concern this consultant evaluates (mode-independent). |
| Verify | Concrete acceptance criteria for the consulting verifier. |

## Verdict Types

Consulting teams produce one of two verdicts:
- **VERIFIED** — output was reviewed, findings within the consultant's focus were found and assessed
- **NOT-APPLICABLE** — output was reviewed, nothing within the consultant's focus was found (with evidence of review)

## Validation Rules

| ID | Rule | Severity |
|----|------|----------|
| CT01 | File has valid YAML frontmatter with `---` delimiters | FAIL |
| CT02 | name field matches `[a-z][a-z0-9]*(-[a-z0-9]+)*` and matches filename | FAIL |
| CT03 | `type: consulting` present in frontmatter | FAIL |
| CT04 | source field is a non-empty list | WARN |
| CT05 | version field is valid semver (`N.N.N`) | FAIL |
| CT06 | Consulting Focus section exists and is non-empty | WARN |
| CT07 | Verify section exists and is non-empty | WARN |
