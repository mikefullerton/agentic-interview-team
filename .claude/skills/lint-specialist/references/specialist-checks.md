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
- **Rule**: Must contain `## Role`, `## Persona`, `## Cookbook Sources`, `## Specialty Teams` in that order
- **Check**: Extract all `## ` headings, verify the 4 required headings appear in order (other headings may appear between them)
- **Fix**: Add missing sections or reorder

### S03 — Team fields complete
- **Severity**: FAIL
- **Rule**: Every `### team-name` under `## Specialty Teams` must have all 3 fields: Artifact, Worker focus, Verify
- **Check**: For each `### ` heading after `## Specialty Teams`, scan until next `### ` or `## ` for all 3 field prefixes
- **Fix**: Add missing fields

### S04 — Team names kebab-case
- **Severity**: FAIL
- **Rule**: Team names must match `[a-z][a-z0-9]*(-[a-z0-9]+)*`
- **Check**: Extract text after `### ` in the Specialty Teams section, validate against pattern
- **Fix**: Rename to kebab-case

### S05 — Artifact paths backtick-wrapped
- **Severity**: FAIL
- **Rule**: Artifact field must contain a backtick-wrapped path
- **Check**: The `- **Artifact**:` line contains at least one pair of backticks with content between them
- **Fix**: Wrap the path in backticks

### S06 — Single-line field values
- **Severity**: WARN
- **Rule**: Worker focus and Verify should be single-line (the parser only captures one line)
- **Check**: The line after `- **Worker focus**:` or `- **Verify**:` that starts with `- **` or `###` or `##` — if neither appears on the next non-blank line, the field may span multiple lines
- **Fix**: Consolidate to a single line

### S07 — No unescaped double quotes
- **Severity**: FAIL
- **Rule**: Worker focus and Verify fields must not contain `"` (breaks JSON output)
- **Check**: Search for `"` in the text after `- **Worker focus**: ` and `- **Verify**: `
- **Fix**: Replace `"` with single quotes or remove

## Content Checks (C-series)

### C01 — Cookbook Sources fully covered by teams
- **Severity**: FAIL
- **Rule**: Every file path in Cookbook Sources must have a corresponding specialty-team
- **Check**: For each path in Cookbook Sources:
  - If it's a file path: there must be a team with that exact Artifact
  - If it's a directory: every `.md` file in that directory (in the cookbook repo) should have a team
- **Note**: Requires `cookbook_repo` from config to resolve directory contents. If unavailable, skip directory expansion and only check explicit file paths.

### C02 — Team artifacts traced to Cookbook Sources
- **Severity**: WARN
- **Rule**: Every specialty-team's Artifact should appear in Cookbook Sources (or its parent directory should)
- **Check**: For each team's Artifact path, verify it (or its parent directory) is listed in Cookbook Sources

### C03 — Artifact paths exist in cookbook
- **Severity**: WARN
- **Rule**: Artifact paths should resolve to real files
- **Check**: Resolve `<cookbook_repo>/<artifact_path>` and verify it exists on disk
- **Note**: Requires `cookbook_repo` from config. If unavailable, skip.

### C04 — At least one team
- **Severity**: FAIL
- **Rule**: `## Specialty Teams` must contain at least one `### team-name`
- **Check**: Count `### ` headings in the Specialty Teams section

### C05 — Exploratory Prompts format
- **Severity**: WARN
- **Rule**: If `## Exploratory Prompts` exists, items should be numbered and end with `?`
- **Check**: Each line matching `^\d+\.` should end with `?`

### C06 — Role non-empty
- **Severity**: FAIL
- **Rule**: Content between `## Role` and the next `##` heading must be non-empty (not just whitespace)
- **Check**: Extract text between `## Role` and next heading, trim, verify non-empty
