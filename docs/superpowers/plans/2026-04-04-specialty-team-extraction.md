# Specialty-Team Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract 229 specialty-teams from 19 specialist markdown files into independent files in a shared `specialty-teams/` pool, with specialist manifests referencing them.

**Architecture:** Each specialty-team becomes its own markdown file with frontmatter (name, description, artifact, version) and body sections (Worker Focus, Verify). Specialists replace their embedded `## Specialty Teams` section with a `## Manifest` listing paths. `run-specialty-teams.sh` is rewritten to read individual files via the manifest.

**Tech Stack:** Shell scripts (bash), markdown, vitest (TypeScript) for tests.

---

## File Structure

### New Files (229 specialty-team files across 19 category directories)

```
specialty-teams/
  accessibility/
    accessibility.md
    accessibility-compliance.md
  claude-code/
    <19 files>
  code-quality/
    <8 files>
  data-persistence/
    <4 files>
  development-process/
    <6 files>
  devops-observability/
    <7 files>
  localization-i18n/
    <3 files>
  networking-api/
    <11 files>
  platform-android/
    <11 files>
  platform-database/
    <3 files>
  platform-ios-apple/
    <12 files>
  platform-web-backend/
    <24 files>
  platform-web-frontend/
    <27 files>
  platform-windows/
    <18 files>
  reliability/
    <3 files>
  security/
    <15 files>
  software-architecture/
    <8 files>
  testing-qa/
    <12 files>
  ui-ux-design/
    <17 files>
```

### New Test File

```
tests/harness/specs/unit/specialty-teams.test.ts
```

### New Scripts (temporary, removed in Task 10)

```
scripts/extract-specialty-teams.sh
scripts/verify-specialty-teams.sh
scripts/add-specialist-manifests.sh
```

### Modified Files

| File | Change |
|------|--------|
| `specialists/*.md` (19 files) | Replace `## Specialty Teams` section with `## Manifest` |
| `scripts/run-specialty-teams.sh` | Rewrite to read manifest + individual files |
| `docs/specialist-spec.md` | Update to reflect new manifest format + specialty-team file spec |
| `docs/specialist-guide.md` | Update architecture description |
| `.claude/skills/lint-specialist/SKILL.md` | Update S02-S07, C01-C04 checks for new format |
| `.claude/skills/lint-specialist/references/specialist-checks.md` | Update check descriptions |
| `.claude/skills/create-specialist/SKILL.md` | Update to create manifest + team files |
| `skills/dev-team/workflows/generate.md` | Update references to run-specialty-teams.sh behavior |

---

## Task 1: Write the extraction script

Write a shell script that reads all 19 specialist files and produces the specialty-team files.

**Files:**
- Create: `scripts/extract-specialty-teams.sh`

- [ ] **Step 1: Write the extraction script**

```bash
#!/bin/bash
# extract-specialty-teams.sh — One-time migration: extract embedded specialty-teams
# into individual files under specialty-teams/<category>/
#
# Usage: extract-specialty-teams.sh
#
# Reads all specialists/*.md files, parses their ## Specialty Teams sections,
# and writes each team to specialty-teams/<category>/<team-name>.md with frontmatter.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPECIALISTS_DIR="$REPO_ROOT/specialists"
OUTPUT_DIR="$REPO_ROOT/specialty-teams"

if [[ ! -d "$SPECIALISTS_DIR" ]]; then
    echo "ERROR: specialists/ directory not found at $SPECIALISTS_DIR" >&2
    exit 1
fi

total_teams=0
total_specialists=0

for specialist_file in "$SPECIALISTS_DIR"/*.md; do
    specialist_name=$(basename "$specialist_file" .md)
    category_dir="$OUTPUT_DIR/$specialist_name"

    # Check if this specialist has a Specialty Teams section
    if ! grep -q "^## Specialty Teams" "$specialist_file"; then
        echo "SKIP: $specialist_name (no Specialty Teams section)"
        continue
    fi

    mkdir -p "$category_dir"
    total_specialists=$((total_specialists + 1))

    # Parse the specialist file
    in_teams=false
    current_name=""
    current_artifact=""
    current_focus=""
    current_verify=""
    team_count=0

    flush_team() {
        if [[ -z "$current_name" ]]; then
            return
        fi

        # Generate description from worker_focus (first ~120 chars)
        description=$(echo "$current_focus" | cut -c1-120)
        if [[ ${#current_focus} -gt 120 ]]; then
            description="${description}..."
        fi

        local team_file="$category_dir/${current_name}.md"
        cat > "$team_file" << TEAMEOF
---
name: $current_name
description: $description
artifact: $current_artifact
version: 1.0.0
---

## Worker Focus
$current_focus

## Verify
$current_verify
TEAMEOF

        team_count=$((team_count + 1))
        total_teams=$((total_teams + 1))
    }

    while IFS= read -r line; do
        if echo "$line" | grep -q "^## Specialty Teams"; then
            in_teams=true
            continue
        fi

        if $in_teams && echo "$line" | grep -q "^## " && ! echo "$line" | grep -q "^## Specialty Teams"; then
            flush_team
            break
        fi

        if ! $in_teams; then
            continue
        fi

        if echo "$line" | grep -q "^### "; then
            flush_team
            current_name=$(echo "$line" | sed 's/^### //')
            current_artifact=""
            current_focus=""
            current_verify=""
            continue
        fi

        if echo "$line" | grep -q "^\- \*\*Artifact\*\*:"; then
            current_artifact=$(echo "$line" | sed 's/.*`\(.*\)`.*/\1/')
            continue
        fi

        if echo "$line" | grep -q "^\- \*\*Worker focus\*\*:"; then
            current_focus=$(echo "$line" | sed 's/.*\*\*Worker focus\*\*: //')
            continue
        fi

        if echo "$line" | grep -q "^\- \*\*Verify\*\*:"; then
            current_verify=$(echo "$line" | sed 's/.*\*\*Verify\*\*: //')
            continue
        fi
    done < "$specialist_file"

    # Flush last team if EOF while in teams section
    if $in_teams && [[ -n "$current_name" ]]; then
        flush_team
    fi

    echo "OK: $specialist_name — $team_count teams extracted to $category_dir/"
done

echo ""
echo "Done: $total_teams teams extracted from $total_specialists specialists"
```

- [ ] **Step 2: Make executable and run**

Run: `chmod +x scripts/extract-specialty-teams.sh && ./scripts/extract-specialty-teams.sh`

Expected: Output showing each specialist processed with team counts, total of ~229 teams across 19 specialists.

- [ ] **Step 3: Verify output structure**

Run: `find specialty-teams -name '*.md' | wc -l`

Expected: 229 (or close — verify against actual specialist contents).

Run: `ls specialty-teams/` to verify 19 category directories exist.

Run: `head -12 specialty-teams/security/authentication.md` to spot-check one file has correct frontmatter and sections.

- [ ] **Step 4: Commit**

```bash
git add scripts/extract-specialty-teams.sh specialty-teams/
git commit -m "Extract 229 specialty-teams into individual files

One-time migration script reads all 19 specialist files and writes
each specialty-team to specialty-teams/<category>/<name>.md with
frontmatter (name, description, artifact, version) and body sections
(Worker Focus, Verify). Existing specialists are unchanged."
git push
```

---

## Task 2: Write verification script

Write a script that compares the extracted files against the embedded originals to ensure nothing was lost or corrupted.

**Files:**
- Create: `scripts/verify-specialty-teams.sh`

- [ ] **Step 1: Write the verification script**

```bash
#!/bin/bash
# verify-specialty-teams.sh — Compare extracted specialty-team files against
# embedded originals in specialist files. Reports mismatches.
#
# Usage: verify-specialty-teams.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPECIALISTS_DIR="$REPO_ROOT/specialists"
TEAMS_DIR="$REPO_ROOT/specialty-teams"

# Temp files for tallying across subshells
ERROR_FILE=$(mktemp)
WARN_FILE=$(mktemp)
TEAM_FILE=$(mktemp)
trap "rm -f $ERROR_FILE $WARN_FILE $TEAM_FILE" EXIT

for specialist_file in "$SPECIALISTS_DIR"/*.md; do
    specialist_name=$(basename "$specialist_file" .md)
    category_dir="$TEAMS_DIR/$specialist_name"

    if ! grep -q "^## Specialty Teams" "$specialist_file"; then
        continue
    fi

    # Get the expected teams from run-specialty-teams.sh (the source of truth parser)
    expected_json=$("$REPO_ROOT/scripts/run-specialty-teams.sh" "$specialist_file")

    # Check category directory exists
    if [[ ! -d "$category_dir" ]]; then
        echo "FAIL: $specialist_name — category directory missing: $category_dir"
        echo "E" >> "$ERROR_FILE"
        continue
    fi

    # Parse expected JSON and check each team
    echo "$expected_json" | grep '"name"' | while IFS= read -r json_line; do
        name=$(echo "$json_line" | sed 's/.*"name": "\([^"]*\)".*/\1/')
        artifact=$(echo "$json_line" | sed 's/.*"artifact": "\([^"]*\)".*/\1/')
        worker_focus=$(echo "$json_line" | sed 's/.*"worker_focus": "\([^"]*\)".*/\1/')
        verify=$(echo "$json_line" | sed 's/.*"verify": "\([^"]*\)".*/\1/')

        team_file="$category_dir/${name}.md"

        if [[ ! -f "$team_file" ]]; then
            echo "FAIL: $specialist_name/$name — file missing: $team_file"
            echo "E" >> "$ERROR_FILE"
            continue
        fi

        # Check artifact in frontmatter
        file_artifact=$(grep "^artifact:" "$team_file" | sed 's/^artifact: //')
        if [[ "$file_artifact" != "$artifact" ]]; then
            echo "FAIL: $specialist_name/$name — artifact mismatch"
            echo "  expected: $artifact"
            echo "  got:      $file_artifact"
            echo "E" >> "$ERROR_FILE"
        fi

        # Check worker_focus in body
        file_focus=$(sed -n '/^## Worker Focus$/,/^## /{/^## /!p}' "$team_file" | sed '/^$/d')
        if [[ "$file_focus" != "$worker_focus" ]]; then
            echo "WARN: $specialist_name/$name — worker_focus differs (may be formatting)"
            echo "W" >> "$WARN_FILE"
        fi

        # Check verify in body
        file_verify=$(sed -n '/^## Verify$/,/^$/p' "$team_file" | tail -n +2 | sed '/^$/d')
        if [[ "$file_verify" != "$verify" ]]; then
            echo "WARN: $specialist_name/$name — verify differs (may be formatting)"
            echo "W" >> "$WARN_FILE"
        fi

        echo "T" >> "$TEAM_FILE"
    done

    # Count files in category that aren't expected (orphans)
    if [[ -d "$category_dir" ]]; then
        for team_file in "$category_dir"/*.md; do
            team_name=$(basename "$team_file" .md)
            if ! echo "$expected_json" | grep -q "\"name\": \"$team_name\""; then
                echo "WARN: $specialist_name/$team_name — orphan file (not in specialist)"
                echo "W" >> "$WARN_FILE"
            fi
        done
    fi
done

# Tally from temp files
errors=$(wc -l < "$ERROR_FILE" | tr -d ' ')
warnings=$(wc -l < "$WARN_FILE" | tr -d ' ')
teams_checked=$(wc -l < "$TEAM_FILE" | tr -d ' ')

echo ""
echo "Checked: $teams_checked teams"
echo "Errors: $errors"
echo "Warnings: $warnings"

if [[ "$errors" -gt 0 ]]; then
    echo "RESULT: FAIL"
    exit 1
else
    echo "RESULT: PASS"
    exit 0
fi
```

- [ ] **Step 2: Make executable and run**

Run: `chmod +x scripts/verify-specialty-teams.sh && ./scripts/verify-specialty-teams.sh`

Expected: All teams checked, 0 errors. Warnings about formatting differences are acceptable (the extracted files use section headings instead of inline fields).

- [ ] **Step 3: Fix any errors found**

If verification reports FAIL errors, fix the extraction script and re-run Task 1 Step 2 and Task 2 Step 2 until PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/verify-specialty-teams.sh
git commit -m "Add specialty-team verification script

Compares extracted files against embedded originals using
run-specialty-teams.sh as the source of truth parser. Checks
artifact paths, worker_focus, and verify content."
git push
```

---

## Task 3: Write unit tests for specialty-team files

Structural validation that every specialty-team file has valid frontmatter, required sections, and correct format.

**Files:**
- Create: `tests/harness/specs/unit/specialty-teams.test.ts`

- [ ] **Step 1: Write the test file**

```typescript
/**
 * Specialty-team file validation — verifies every file in specialty-teams/
 * has valid frontmatter and required sections.
 */

import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync, existsSync } from "fs";
import { join, basename } from "path";

const REPO_ROOT = join(__dirname, "../../../..");
const TEAMS_DIR = join(REPO_ROOT, "specialty-teams");
const SPECIALISTS_DIR = join(REPO_ROOT, "specialists");

// Collect all specialty-team files
function getAllTeamFiles(): { category: string; name: string; path: string }[] {
  const files: { category: string; name: string; path: string }[] = [];
  if (!existsSync(TEAMS_DIR)) return files;

  for (const category of readdirSync(TEAMS_DIR)) {
    const categoryPath = join(TEAMS_DIR, category);
    if (!statSync(categoryPath).isDirectory()) continue;

    for (const file of readdirSync(categoryPath)) {
      if (!file.endsWith(".md")) continue;
      files.push({
        category,
        name: basename(file, ".md"),
        path: join(categoryPath, file),
      });
    }
  }
  return files;
}

// Parse frontmatter from a markdown file
function parseFrontmatter(
  content: string
): { fields: Record<string, string>; body: string } | null {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return null;

  const fields: Record<string, string> = {};
  for (const line of match[1].split("\n")) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    const value = line.slice(colonIdx + 1).trim();
    fields[key] = value;
  }
  return { fields, body: match[2] };
}

const teamFiles = getAllTeamFiles();

describe("specialty-teams directory structure", () => {
  it("has at least one category directory", () => {
    const categories = readdirSync(TEAMS_DIR).filter((f) =>
      statSync(join(TEAMS_DIR, f)).isDirectory()
    );
    expect(categories.length).toBeGreaterThan(0);
  });

  it("every category corresponds to a specialist", () => {
    const categories = readdirSync(TEAMS_DIR).filter((f) =>
      statSync(join(TEAMS_DIR, f)).isDirectory()
    );
    for (const category of categories) {
      const specialistFile = join(SPECIALISTS_DIR, `${category}.md`);
      expect(
        existsSync(specialistFile),
        `Category ${category} has no matching specialist file`
      ).toBe(true);
    }
  });

  it("has the expected number of team files", () => {
    expect(teamFiles.length).toBeGreaterThanOrEqual(220);
  });
});

describe.each(teamFiles)(
  "specialty-teams/$category/$name.md",
  ({ category, name, path }) => {
    const content = readFileSync(path, "utf-8");
    const parsed = parseFrontmatter(content);

    it("has valid frontmatter", () => {
      expect(parsed, "Missing or malformed frontmatter").not.toBeNull();
    });

    it("has required frontmatter fields", () => {
      expect(parsed!.fields).toHaveProperty("name");
      expect(parsed!.fields).toHaveProperty("description");
      expect(parsed!.fields).toHaveProperty("artifact");
      expect(parsed!.fields).toHaveProperty("version");
    });

    it("name field matches filename", () => {
      expect(parsed!.fields.name).toBe(name);
    });

    it("name is kebab-case", () => {
      expect(name).toMatch(/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/);
    });

    it("artifact is a non-empty path", () => {
      expect(parsed!.fields.artifact.length).toBeGreaterThan(0);
      expect(parsed!.fields.artifact).toMatch(/\.md$/);
    });

    it("version is semver", () => {
      expect(parsed!.fields.version).toMatch(/^\d+\.\d+\.\d+$/);
    });

    it("description is non-empty", () => {
      expect(parsed!.fields.description.length).toBeGreaterThan(0);
    });

    it("has Worker Focus section", () => {
      expect(parsed!.body).toContain("## Worker Focus");
    });

    it("has Verify section", () => {
      expect(parsed!.body).toContain("## Verify");
    });

    it("Worker Focus section is non-empty", () => {
      const match = parsed!.body.match(
        /## Worker Focus\n([\s\S]*?)(?=\n## |\n*$)/
      );
      expect(match, "Worker Focus section not found").not.toBeNull();
      expect(match![1].trim().length).toBeGreaterThan(0);
    });

    it("Verify section is non-empty", () => {
      const match = parsed!.body.match(
        /## Verify\n([\s\S]*?)(?=\n## |\n*$)/
      );
      expect(match, "Verify section not found").not.toBeNull();
      expect(match![1].trim().length).toBeGreaterThan(0);
    });
  }
);
```

- [ ] **Step 2: Run the tests**

Run: `cd tests/harness && npx vitest run specs/unit/specialty-teams.test.ts`

Expected: All tests pass. If any fail, the extraction script produced malformed files — fix the script, re-extract, and re-run.

- [ ] **Step 3: Fix any failures and re-run until green**

- [ ] **Step 4: Commit**

```bash
git add tests/harness/specs/unit/specialty-teams.test.ts
git commit -m "Add unit tests for extracted specialty-team files

Validates frontmatter (name, description, artifact, version),
body sections (Worker Focus, Verify), naming conventions, and
directory-to-specialist correspondence for all 229 team files."
git push
```

---

## Task 4: Add manifests to specialists

Replace the `## Specialty Teams` embedded sections with `## Manifest` sections listing paths to the extracted files.

**Files:**
- Modify: `specialists/*.md` (19 files)

- [ ] **Step 1: Write a script to add manifests**

Create `scripts/add-specialist-manifests.sh`:

```bash
#!/bin/bash
# add-specialist-manifests.sh — Replace ## Specialty Teams sections with ## Manifest
# listing paths to extracted specialty-team files.
#
# Usage: add-specialist-manifests.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPECIALISTS_DIR="$REPO_ROOT/specialists"
TEAMS_DIR="$REPO_ROOT/specialty-teams"

for specialist_file in "$SPECIALISTS_DIR"/*.md; do
    specialist_name=$(basename "$specialist_file" .md)
    category_dir="$TEAMS_DIR/$specialist_name"

    if ! grep -q "^## Specialty Teams" "$specialist_file"; then
        echo "SKIP: $specialist_name (no Specialty Teams section)"
        continue
    fi

    if [[ ! -d "$category_dir" ]]; then
        echo "ERROR: $specialist_name — no category dir at $category_dir" >&2
        continue
    fi

    # Build manifest list
    manifest_lines=""
    for team_file in "$category_dir"/*.md; do
        team_name=$(basename "$team_file" .md)
        manifest_lines="${manifest_lines}- specialty-teams/${specialist_name}/${team_name}.md\n"
    done

    # Build new file content:
    # 1. Everything before ## Specialty Teams
    # 2. ## Manifest with paths
    # 3. Everything after the Specialty Teams section (Exploratory Prompts, etc.)

    before=$(sed -n '1,/^## Specialty Teams$/p' "$specialist_file" | head -n -1)
    
    # Find what comes after Specialty Teams section
    # (next ## heading that isn't Specialty Teams, through EOF)
    after_line=$(grep -n "^## " "$specialist_file" | grep -v "Specialty Teams" | awk -F: -v st="$(grep -n "^## Specialty Teams" "$specialist_file" | cut -d: -f1)" '$1 > st {print $1; exit}')
    
    if [[ -n "$after_line" ]]; then
        after=$(tail -n +"$after_line" "$specialist_file")
    else
        after=""
    fi

    # Write new file
    {
        echo "$before"
        echo ""
        echo "## Manifest"
        echo ""
        printf "$manifest_lines"
        if [[ -n "$after" ]]; then
            echo ""
            echo "$after"
        fi
    } > "$specialist_file"

    team_count=$(find "$category_dir" -name '*.md' | wc -l | tr -d ' ')
    echo "OK: $specialist_name — manifest with $team_count team references"
done
```

- [ ] **Step 2: Run the manifest script**

Run: `chmod +x scripts/add-specialist-manifests.sh && ./scripts/add-specialist-manifests.sh`

Expected: Each specialist reports OK with correct team count.

- [ ] **Step 3: Spot-check a specialist file**

Run: `cat specialists/security.md` and verify:
- `## Specialty Teams` section is gone
- `## Manifest` section exists with 15 paths
- Other sections (Role, Persona, Cookbook Sources, Exploratory Prompts) are intact

- [ ] **Step 4: Commit**

```bash
git add specialists/
git commit -m "Replace embedded specialty-teams with manifests in all specialists

Each specialist's ## Specialty Teams section is replaced with ## Manifest
listing paths to the extracted files in specialty-teams/<category>/."
git push
```

---

## Task 5: Rewrite run-specialty-teams.sh

The script currently parses embedded markdown sections. Rewrite it to read the manifest from the specialist file, then read each referenced specialty-team file.

**Files:**
- Modify: `scripts/run-specialty-teams.sh`
- Modify: `tests/harness/specs/unit/specialty-teams.test.ts`

- [ ] **Step 1: Add tests for run-specialty-teams.sh**

Append to `tests/harness/specs/unit/specialty-teams.test.ts`:

```typescript
import { execFileSync } from "child_process";

describe("run-specialty-teams.sh", () => {
  const RUN_SCRIPT = join(REPO_ROOT, "scripts", "run-specialty-teams.sh");

  it("outputs valid JSON for a specialist with manifest", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "accessibility.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    expect(Array.isArray(teams)).toBe(true);
    expect(teams.length).toBe(2);
  });

  it("each team has required fields", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "accessibility.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    for (const team of teams) {
      expect(team).toHaveProperty("name");
      expect(team).toHaveProperty("artifact");
      expect(team).toHaveProperty("worker_focus");
      expect(team).toHaveProperty("verify");
    }
  });

  it("outputs correct team count for security specialist", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "security.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    expect(teams.length).toBe(15);
  });

  it("team fields match file content", () => {
    const result = execFileSync(
      RUN_SCRIPT,
      [join(SPECIALISTS_DIR, "security.md")],
      { encoding: "utf-8" }
    );
    const teams = JSON.parse(result);
    const authTeam = teams.find(
      (t: { name: string }) => t.name === "authentication"
    );
    expect(authTeam).toBeDefined();
    expect(authTeam.artifact).toBe("guidelines/security/authentication.md");
    expect(authTeam.worker_focus.length).toBeGreaterThan(0);
    expect(authTeam.verify.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests/harness && npx vitest run specs/unit/specialty-teams.test.ts`

Expected: The `run-specialty-teams.sh` tests fail because the script still reads embedded format but specialists now have manifests.

- [ ] **Step 3: Rewrite run-specialty-teams.sh**

Replace `scripts/run-specialty-teams.sh` with:

```bash
#!/bin/bash
# run-specialty-teams.sh — Read specialty-team definitions for a specialist
#
# Reads the specialist's ## Manifest section, resolves each path to a
# specialty-team file, parses its frontmatter and body sections, and
# outputs a JSON array.
#
# Usage:
#   run-specialty-teams.sh <specialist-file> [--mode <mode>]
#
# Output: JSON array of specialty-team definitions
#   [
#     {
#       "name": "authentication",
#       "artifact": "guidelines/security/authentication.md",
#       "worker_focus": "OAuth 2.0/OIDC with PKCE...",
#       "verify": "Auth method chosen, PKCE for public clients..."
#     },
#     ...
#   ]

set -euo pipefail

SPECIALIST_FILE="${1:?Usage: run-specialty-teams.sh <specialist-file> [--mode <mode>]}"

if [[ ! -f "$SPECIALIST_FILE" ]]; then
    echo "ERROR: Specialist file not found: $SPECIALIST_FILE" >&2
    exit 1
fi

# Resolve repo root from specialist file location
REPO_ROOT="$(cd "$(dirname "$SPECIALIST_FILE")/.." && pwd)"

# Escape double quotes and backslashes for JSON string values
json_escape() {
    echo "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

# Collect manifest paths from the specialist file
manifest_paths=()
in_manifest=false

while IFS= read -r line; do
    if echo "$line" | grep -q "^## Manifest"; then
        in_manifest=true
        continue
    fi

    if $in_manifest && echo "$line" | grep -q "^## "; then
        break
    fi

    if $in_manifest && echo "$line" | grep -q "^- "; then
        path=$(echo "$line" | sed 's/^- //')
        manifest_paths+=("$path")
    fi
done < "$SPECIALIST_FILE"

if [[ ${#manifest_paths[@]} -eq 0 ]]; then
    echo "ERROR: No manifest entries found in $SPECIALIST_FILE" >&2
    exit 1
fi

# Read each specialty-team file and output JSON
first=true
echo "["

for team_path in "${manifest_paths[@]}"; do
    team_file="$REPO_ROOT/$team_path"

    if [[ ! -f "$team_file" ]]; then
        echo "ERROR: Specialty-team file not found: $team_file" >&2
        exit 1
    fi

    # Parse frontmatter
    name=""
    artifact=""
    in_frontmatter=false

    while IFS= read -r line; do
        if [[ "$line" == "---" ]] && ! $in_frontmatter; then
            in_frontmatter=true
            continue
        fi
        if [[ "$line" == "---" ]] && $in_frontmatter; then
            break
        fi
        if $in_frontmatter; then
            case "$line" in
                name:*) name=$(echo "$line" | sed 's/^name: *//') ;;
                artifact:*) artifact=$(echo "$line" | sed 's/^artifact: *//') ;;
            esac
        fi
    done < "$team_file"

    # Parse body sections
    worker_focus=""
    verify=""
    current_section=""

    while IFS= read -r line; do
        if [[ "$line" == "## Worker Focus" ]]; then
            current_section="focus"
            continue
        fi
        if [[ "$line" == "## Verify" ]]; then
            current_section="verify"
            continue
        fi
        if echo "$line" | grep -q "^## "; then
            current_section=""
            continue
        fi

        # Skip empty lines at section start
        if [[ -z "$line" ]] && [[ -z "$worker_focus" ]] && [[ "$current_section" == "focus" ]]; then
            continue
        fi
        if [[ -z "$line" ]] && [[ -z "$verify" ]] && [[ "$current_section" == "verify" ]]; then
            continue
        fi

        case "$current_section" in
            focus) worker_focus="$line" ;;
            verify) verify="$line" ;;
        esac
    done < "$team_file"

    if ! $first; then echo ","; fi
    printf '  {"name": "%s", "artifact": "%s", "worker_focus": "%s", "verify": "%s"}' \
        "$(json_escape "$name")" "$(json_escape "$artifact")" "$(json_escape "$worker_focus")" "$(json_escape "$verify")"
    first=false
done

echo ""
echo "]"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests/harness && npx vitest run specs/unit/specialty-teams.test.ts`

Expected: All tests pass including the new `run-specialty-teams.sh` tests.

- [ ] **Step 5: Commit**

```bash
git add scripts/run-specialty-teams.sh tests/harness/specs/unit/specialty-teams.test.ts
git commit -m "Rewrite run-specialty-teams.sh to read from manifest + individual files

Reads specialist's ## Manifest section, resolves paths to specialty-team
files, parses frontmatter and body sections, outputs same JSON format.
Includes tests verifying output structure and team counts."
git push
```

---

## Task 6: Update docs and specs

Update `docs/specialist-spec.md` and `docs/specialist-guide.md` to reflect the new structure.

**Files:**
- Modify: `docs/specialist-spec.md`
- Modify: `docs/specialist-guide.md`

- [ ] **Step 1: Update specialist-spec.md**

In `docs/specialist-spec.md`:

1. Replace section `### 5. Specialty Teams` with a new `### 5. Manifest` section:

```markdown
### 5. Manifest

\`\`\`markdown
## Manifest
- specialty-teams/<category>/<team-name>.md
- specialty-teams/<category>/<team-name>.md
\`\`\`

- Markdown list of paths to specialty-team files, relative to the repo root
- Each path MUST resolve to an existing file in `specialty-teams/`
- At least one entry required
```

2. Replace the `## Specialty Team Entry` section with a new `## Specialty-Team File Specification` section:

```markdown
## Specialty-Team File Specification

Each specialty-team is a standalone markdown file in `specialty-teams/<category>/<name>.md`.

### File Location

`specialty-teams/<category>/<name>.md` where:
- `<category>` matches a specialist filename in `specialists/` (e.g., `security`, `platform-ios-apple`)
- `<name>` is lowercase kebab-case, typically derived from the artifact filename

### Frontmatter

\`\`\`yaml
---
name: <kebab-case-name>
description: <human-readable description of what this team covers>
artifact: <path to one cookbook artifact, relative to cookbook root>
version: <semver>
---
\`\`\`

| Field | Format | Description |
|-------|--------|-------------|
| name | `[a-z][a-z0-9]*(-[a-z0-9]+)*` | Unique within category, matches filename |
| description | Free text, ~120 chars | Human-readable summary for discovery |
| artifact | Cookbook-relative path ending in `.md` | Single file path (not a directory) |
| version | `N.N.N` semver | Tracks changes to this team definition |

### Body Sections

\`\`\`markdown
## Worker Focus
<text>

## Verify
<text>
\`\`\`

| Section | Description |
|---------|-------------|
| Worker Focus | What this team cares about (mode-independent). Guides the worker agent. |
| Verify | Concrete acceptance criteria. The verifier uses this to determine PASS/FAIL. |
```

3. Update `## Validation Rules` — S-series and C-series checks:
   - S02: Required sections are `## Role`, `## Persona`, `## Cookbook Sources`, `## Manifest` in order
   - S03: Each manifest path resolves to a file with valid frontmatter (name, description, artifact, version) and body sections (Worker Focus, Verify)
   - S04: name field in each referenced team file matches `[a-z][a-z0-9]*(-[a-z0-9]+)*`
   - S05: artifact field in each referenced team file is non-empty and ends with `.md`
   - S06: Worker Focus and Verify sections are non-empty
   - S07: Remove (no longer relevant)
   - C01: Every file path in Cookbook Sources has a corresponding team in the manifest (resolve through team files' artifact fields)
   - C02: Every manifest team's artifact appears in Cookbook Sources (or its parent directory)
   - C04: Manifest has at least one entry

4. Update `## Parser Contract`:

```markdown
## Parser Contract

`scripts/run-specialty-teams.sh` reads specialist files and outputs a JSON array. It relies on:

- `## Manifest` heading to enter manifest reading
- `- ` prefixed lines to collect team file paths
- Next `## ` heading or EOF to exit manifest reading
- For each referenced file: YAML frontmatter for `name` and `artifact`, `## Worker Focus` and `## Verify` body sections for content
- Outputs one JSON object per team with fields: name, artifact, worker_focus, verify
```

5. Update the `## Example` section to show the new format with a manifest and separate team files.

- [ ] **Step 2: Update specialist-guide.md**

Read the file, find sections describing specialty-team structure and execution. Update:
- Specialty-teams are independent files in `specialty-teams/<category>/`
- Specialists reference them via `## Manifest`
- `run-specialty-teams.sh` reads manifest, then reads each team file
- The JSON output format is unchanged

- [ ] **Step 3: Commit**

```bash
git add docs/specialist-spec.md docs/specialist-guide.md
git commit -m "Update specialist spec and guide for extracted specialty-teams

Reflects new structure: ## Manifest in specialists, individual files in
specialty-teams/<category>/, updated validation rules and parser contract."
git push
```

---

## Task 7: Update lint-specialist and create-specialist skills

**Files:**
- Modify: `.claude/skills/lint-specialist/SKILL.md`
- Modify: `.claude/skills/lint-specialist/references/specialist-checks.md`
- Modify: `.claude/skills/create-specialist/SKILL.md`

- [ ] **Step 1: Update lint-specialist SKILL.md**

Update the structure checks:
- S02: Check for `## Manifest` instead of `## Specialty Teams` in the required sections list
- S03: For each `- ` line in `## Manifest`, resolve the path to a file and check it has valid frontmatter (name, description, artifact, version fields) and body sections (`## Worker Focus`, `## Verify`)
- S04: Check the `name` field in each referenced team file matches `[a-z][a-z0-9]*(-[a-z0-9]+)*`
- S05: Check the `artifact` field in each referenced team file is non-empty and ends with `.md`
- S06: Check `## Worker Focus` and `## Verify` sections in each referenced team file are non-empty
- S07: Remove (JSON escaping no longer relevant — frontmatter handles quoting)

Update content checks:
- C01: For each path in Cookbook Sources, resolve through manifest team files' artifact fields to verify coverage
- C02: For each manifest team's artifact, verify it appears in Cookbook Sources (or parent dir)
- C04: Manifest section has at least one `- ` entry

- [ ] **Step 2: Update specialist-checks.md reference**

Mirror the same changes in `.claude/skills/lint-specialist/references/specialist-checks.md` — update each check's Rule, Check, and Fix descriptions.

- [ ] **Step 3: Update create-specialist SKILL.md**

Read the current file. Update the scaffolding instructions to:
- Create `specialty-teams/<specialist-name>/` directory
- Create individual team files with frontmatter (name, description, artifact, version) and body sections
- Create specialist file with `## Manifest` referencing the team files instead of embedding team definitions

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/lint-specialist/ .claude/skills/create-specialist/
git commit -m "Update lint-specialist and create-specialist for new structure

Lint checks now validate ## Manifest + referenced specialty-team files.
Create scaffolds team files in specialty-teams/<category>/ with manifests."
git push
```

---

## Task 8: Update workflow references

**Files:**
- Modify: `skills/dev-team/workflows/generate.md`

- [ ] **Step 1: Update generate.md**

In the `### 3b. Run Reviews (Specialty-Team Loop)` section, update Step 1 description:

Change from:
> Run `${CLAUDE_PLUGIN_ROOT}/scripts/run-specialty-teams.sh <specialist-file>` to get the JSON array of specialty-teams.

To:
> Run `${CLAUDE_PLUGIN_ROOT}/scripts/run-specialty-teams.sh <specialist-file>` to get the JSON array of specialty-teams. The script reads the specialist's `## Manifest` section and resolves each path to a specialty-team file. The output JSON format is unchanged.

This is a documentation-only update since the JSON output format is identical.

- [ ] **Step 2: Commit**

```bash
git add skills/dev-team/workflows/generate.md
git commit -m "Update generate workflow docs for manifest-based specialty-teams

run-specialty-teams.sh output format is unchanged; updated description
of how it reads from manifest + individual files."
git push
```

---

## Task 9: Add reference integrity tests and run full suite

**Files:**
- Modify: `tests/harness/specs/unit/specialty-teams.test.ts`

- [ ] **Step 1: Add manifest reference integrity tests**

Append to `tests/harness/specs/unit/specialty-teams.test.ts`:

```typescript
describe("specialist manifest integrity", () => {
  const specialistFiles = readdirSync(SPECIALISTS_DIR).filter((f) =>
    f.endsWith(".md")
  );

  describe.each(specialistFiles)("specialists/%s", (filename) => {
    const content = readFileSync(join(SPECIALISTS_DIR, filename), "utf-8");

    it("has a ## Manifest section", () => {
      expect(content).toContain("## Manifest");
    });

    it("manifest paths resolve to existing files", () => {
      const manifestMatch = content.match(
        /## Manifest\n([\s\S]*?)(?=\n## |\n*$)/
      );
      expect(
        manifestMatch,
        `${filename} missing ## Manifest section`
      ).not.toBeNull();

      const paths = manifestMatch![1]
        .split("\n")
        .filter((l) => l.startsWith("- "))
        .map((l) => l.replace(/^- /, ""));

      expect(paths.length).toBeGreaterThan(0);

      for (const p of paths) {
        const fullPath = join(REPO_ROOT, p);
        expect(
          existsSync(fullPath),
          `${filename} references missing file: ${p}`
        ).toBe(true);
      }
    });

    it("no longer has embedded ## Specialty Teams section", () => {
      expect(content).not.toContain("## Specialty Teams");
    });
  });
});
```

- [ ] **Step 2: Run full unit test suite**

Run: `cd tests/harness && npx vitest run --config vitest.unit.config.ts`

Expected: All tests pass.

- [ ] **Step 3: Fix any failures and re-run until green**

- [ ] **Step 4: Commit**

```bash
git add tests/harness/specs/unit/specialty-teams.test.ts
git commit -m "Add manifest reference integrity tests

Verifies every specialist has a ## Manifest section, all referenced
specialty-team files exist, and no embedded ## Specialty Teams remain."
git push
```

---

## Task 10: Clean up migration scripts

Remove the one-time migration scripts that are no longer needed.

**Files:**
- Delete: `scripts/extract-specialty-teams.sh`
- Delete: `scripts/verify-specialty-teams.sh`
- Delete: `scripts/add-specialist-manifests.sh`

- [ ] **Step 1: Remove migration scripts**

```bash
rm scripts/extract-specialty-teams.sh scripts/verify-specialty-teams.sh scripts/add-specialist-manifests.sh
```

- [ ] **Step 2: Run tests one final time**

Run: `cd tests/harness && npx vitest run --config vitest.unit.config.ts`

Expected: All tests pass (no test depends on migration scripts).

- [ ] **Step 3: Commit**

```bash
git add -u scripts/extract-specialty-teams.sh scripts/verify-specialty-teams.sh scripts/add-specialist-manifests.sh
git commit -m "Remove one-time migration scripts

extract-specialty-teams.sh, verify-specialty-teams.sh, and
add-specialist-manifests.sh are no longer needed."
git push
```
