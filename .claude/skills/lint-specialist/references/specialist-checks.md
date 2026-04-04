# Specialist Validation Checks

Reference checklist for `/lint-specialist`. Each check has an ID, description, severity, and how to verify.

## Structure Checks (S-series)

### S01 — Title format
- **Severity**: FAIL
- **Rule**: First line must match `# <Name> Specialist`
- **Check**: Line 1 starts with `# ` and ends with ` Specialist`
- **Fix**: Rename the heading to `# <Name> Specialist`

### S02 — Required sections present and ordered
- **Severity**: FAIL
- **Rule**: Must contain `## Role`, `## Persona`, `## Cookbook Sources`, `## Manifest` in that order
- **Check**: Extract all `## ` headings, verify the 4 required headings appear in order (other headings may appear between them)
- **Fix**: Add missing sections or reorder

### S03 — Manifest team files valid
- **Severity**: FAIL
- **Rule**: Every `- ` path in `## Manifest` must resolve to a file with valid YAML frontmatter (name, description, artifact, version) and body sections (## Worker Focus, ## Verify)
- **Check**: For each `- ` line in the Manifest section, resolve the path relative to the repo root. Read the file. Parse frontmatter and verify all 4 fields exist. Verify `## Worker Focus` and `## Verify` headings exist in the body.
- **Fix**: Create or fix the referenced team file

### S04 — Team names kebab-case and match filename
- **Severity**: FAIL
- **Rule**: The `name` field in each referenced team file must match `[a-z][a-z0-9]*(-[a-z0-9]+)*` and must match the filename (without `.md`)
- **Check**: Read the `name` field from each team file's frontmatter, validate against pattern, compare to filename
- **Fix**: Rename the file and update the `name` field to match

### S05 — Artifact paths valid
- **Severity**: FAIL
- **Rule**: The `artifact` field in each referenced team file must be non-empty and end with `.md`
- **Check**: Read the `artifact` field from each team file's frontmatter
- **Fix**: Fix the artifact path in the team file's frontmatter

### S06 — Worker Focus and Verify sections non-empty
- **Severity**: WARN
- **Rule**: Each referenced team file's `## Worker Focus` and `## Verify` sections must have content
- **Check**: Extract text between `## Worker Focus` and the next `## ` heading (or EOF), trim, verify non-empty. Same for `## Verify`.
- **Fix**: Add content to the empty section

## Content Checks (C-series)

### C01 — Cookbook Sources fully covered by manifest teams
- **Severity**: FAIL
- **Rule**: Every file path in Cookbook Sources must have a corresponding team in the manifest (resolved through team files' artifact fields)
- **Check**: For each path in Cookbook Sources:
  - If it's a file path: there must be a manifest team whose `artifact` field matches
  - If it's a directory: every `.md` file in that directory (in the cookbook repo) should have a manifest team
- **Note**: Requires `cookbook_repo` from config to resolve directory contents. If unavailable, skip directory expansion and only check explicit file paths.

### C02 — Manifest team artifacts traced to Cookbook Sources
- **Severity**: WARN
- **Rule**: Every manifest team's artifact (from team file frontmatter) should appear in Cookbook Sources (or its parent directory should)
- **Check**: For each manifest team's `artifact` field, verify it (or its parent directory) is listed in Cookbook Sources

### C03 — Artifact paths exist in cookbook
- **Severity**: WARN
- **Rule**: Artifact paths in team files should resolve to real files
- **Check**: Resolve `<cookbook_repo>/<artifact_path>` for each manifest team and verify it exists on disk
- **Note**: Requires `cookbook_repo` from config. If unavailable, skip.

### C04 — At least one manifest entry
- **Severity**: FAIL
- **Rule**: `## Manifest` must contain at least one `- ` entry
- **Check**: Count `- ` lines in the Manifest section

### C05 — Exploratory Prompts format
- **Severity**: WARN
- **Rule**: If `## Exploratory Prompts` exists, items should be numbered and end with `?`
- **Check**: Each line matching `^\d+\.` should end with `?`

### C06 — Role non-empty
- **Severity**: FAIL
- **Rule**: Content between `## Role` and the next `##` heading must be non-empty (not just whitespace)
- **Check**: Extract text between `## Role` and next heading, trim, verify non-empty

### C07 — Persona is not placeholder
- **Severity**: WARN
- **Rule**: `## Persona` should not contain only `(coming)` — a full persona definition is preferred
- **Check**: Extract text between `## Persona` and the next `##` heading. If it trims to `(coming)`, flag as WARN.
- **Fix**: Define the persona with Archetype, Voice, Priorities, and optionally Anti-Patterns sub-sections

### C08 — Persona has required sub-sections
- **Severity**: FAIL
- **Rule**: When the Persona section is NOT the `(coming)` placeholder, it MUST contain `### Archetype`, `### Voice`, and `### Priorities` sub-headings
- **Check**: If Persona content is not `(coming)`, scan for the three required `### ` headings within the Persona section
- **Fix**: Add missing sub-sections
