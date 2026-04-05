# Dev-Team Performance Optimization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize the dev-team plugin for speed and token efficiency by extracting deterministic operations to shell scripts, eliminating duplicated guidance across skills, and applying progressive disclosure.

**Architecture:** Create a `scripts/` directory for shared shell scripts (config loading, version checking, specialist assignment). Create reference files for duplicated logic (test mode spec, specialist assignment rules). Update all 5 skills to call scripts and reference files instead of inlining repeated instructions.

**Tech Stack:** Bash shell scripts, jq for JSON processing, existing markdown skill/agent files.

---

## Context

The dev-team plugin has 5 skills (1,677 lines) and 15 agents (2,110 lines). Analysis against the cookbook's performance guideline (`cookbook/guidelines/skills-and-agents/performance.md`) found:

- **~330 lines of duplicated guidance** across skills (config loading 5x, version check 5x, specialist assignment 3x, test mode 5x)
- **Deterministic operations using model tokens** instead of shell scripts (config migration, version extraction, JSON validation, build system selection)
- **On-demand content inlined** that should be loaded progressively (test mode spec, specialist assignment rules)

This plan applies the three performance principles: shell scripts for deterministic work, eliminate duplication via reference files, progressive disclosure of context.

---

## File Structure

### New files to create

```
scripts/
  load-config.sh              # Config loading, migration, validation
  version-check.sh            # Extract version from SKILL.md, compare
  assign-specialists.sh       # Specialist assignment from JSON mappings
research/
  specialist-assignment.md    # Single source of truth for assignment rules + tier ordering
  specialist-assignment.json  # Machine-readable assignment mappings
```

### Files to modify

```
skills/interview/SKILL.md     # Replace config/version boilerplate, reference test mode spec
skills/create-recipe-from-code/SKILL.md       # Replace config/version boilerplate, reference test mode spec
skills/generate/SKILL.md      # Replace config/version/assignment boilerplate, reference test mode spec
skills/build/SKILL.md         # Replace config/version/assignment boilerplate, reference test mode spec
skills/lint/SKILL.md          # Replace config/version/assignment boilerplate, reference test mode spec
tests/test-mode-spec.md       # Consolidate as the single test mode reference (already exists)
```

---

## Task 1: Create shell scripts directory and config loader

**Files:**
- Create: `scripts/load-config.sh`
- Create: `scripts/version-check.sh`

- [ ] **Step 1:** Create `scripts/` directory

```bash
mkdir -p /Users/mfullerton/projects/agentic-cookbook/dev-team/scripts
```

- [ ] **Step 2:** Create `scripts/load-config.sh`

```bash
#!/bin/bash
# load-config.sh — Load and migrate dev-team configuration
# Usage: load-config.sh [--config <path>]
# Outputs: JSON config to stdout, errors to stderr
# Exit codes: 0 = success, 1 = config not found or invalid

set -euo pipefail

CONFIG_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

NEW_CONFIG="${HOME}/.agentic-cookbook/dev-team/config.json"
OLD_CONFIG="${HOME}/.agentic-interviewer/config.json"

if [[ -z "$CONFIG_PATH" ]]; then
  CONFIG_PATH="$NEW_CONFIG"
fi

# Migrate from old location if needed
if [[ ! -f "$CONFIG_PATH" && -f "$OLD_CONFIG" ]]; then
  mkdir -p "$(dirname "$CONFIG_PATH")"
  jq '{
    workspace_repo: .interview_repo,
    cookbook_repo: .cookbook_repo,
    user_name: .user_name,
    authorized_repos: (.authorized_repos // [])
  }' "$OLD_CONFIG" > "$CONFIG_PATH"
  echo "Migrated config from $OLD_CONFIG to $CONFIG_PATH" >&2
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found at $CONFIG_PATH" >&2
  exit 1
fi

# Validate required fields
if ! jq -e '.workspace_repo and .cookbook_repo and .user_name' "$CONFIG_PATH" > /dev/null 2>&1; then
  echo "Config missing required fields (workspace_repo, cookbook_repo, user_name)" >&2
  exit 1
fi

cat "$CONFIG_PATH"
```

- [ ] **Step 3:** Create `scripts/version-check.sh`

```bash
#!/bin/bash
# version-check.sh — Compare running version against installed SKILL.md
# Usage: version-check.sh <skill-dir> <running-version>
# Outputs: Warning to stderr if versions differ, nothing if they match

SKILL_DIR="$1"
RUNNING_VERSION="$2"

if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
  exit 0
fi

INSTALLED_VERSION=$(
  awk '/^---$/{ if (++n==2) exit } /^version: / && n==1 { sub(/^version: /, ""); print }' "$SKILL_DIR/SKILL.md"
)

if [[ -n "$INSTALLED_VERSION" && "$INSTALLED_VERSION" != "$RUNNING_VERSION" ]]; then
  echo "Warning: This skill is running v${RUNNING_VERSION} but v${INSTALLED_VERSION} is installed. Restart the session to use the latest version."
fi
```

- [ ] **Step 4:** Make scripts executable

```bash
chmod +x scripts/load-config.sh scripts/version-check.sh
```

- [ ] **Step 5:** Commit and push

```bash
git add scripts/
git commit -m "Add shell scripts for config loading and version checking

Deterministic operations extracted per cookbook performance guideline:
config migration, validation, and version comparison."
git push
```

---

## Task 2: Create specialist assignment reference and JSON

**Files:**
- Create: `research/specialist-assignment.md`
- Create: `research/specialist-assignment.json`
- Create: `scripts/assign-specialists.sh`

- [ ] **Step 1:** Create `research/specialist-assignment.md` — the single source of truth for assignment logic, extracted from the generate/build/lint skills. Content:

```markdown
# Specialist Assignment Rules

Determines which specialists review or augment each recipe. Used by the generate, build, and lint skills.

## Assignment Logic

For each recipe, assign specialists based on three criteria applied in order:

### 1. Recipe Category → Domain Specialists

| Category Pattern | Specialists |
|-----------------|------------|
| `recipe.ui.*` | UI/UX & Design, Accessibility |
| `recipe.infrastructure.*` | Software Architecture, Code Quality |
| `recipe.app.*` | Software Architecture, Development Process |
| All recipes with behavioral requirements | Reliability & Error Handling |

### 2. Recipe Content → Additional Specialists

Scan the recipe for keywords and add specialists:

| Keywords | Specialist |
|----------|-----------|
| auth, tokens, credentials | Security |
| network, API, endpoint, HTTP | Networking & API |
| storage, persistence, database, cache | Data & Persistence |
| logging, analytics, monitoring | DevOps & Observability |
| localization, i18n, RTL, locale | Localization & I18n |
| test, testing, verification | Testing & QA |
| claude, skill, rule, agent, hook, MCP | Claude Code & Agentic Development |

### 3. Project Platforms → Platform Specialists

From `cookbook-project.json` `platforms` array:

| Platform | Specialist |
|----------|-----------|
| ios, macos | platform-ios-apple |
| android | platform-android |
| windows | platform-windows |
| web | platform-web-frontend, platform-web-backend |

### Limits

Assign at most **3-4 specialists per recipe**. Priority: domain specialist most related to recipe category → platform specialists → cross-cutting specialists.

## Specialist Tier Ordering (Build Only)

When specialists augment code sequentially in the build workflow, order by tier:

| Tier | Role | Specialists |
|------|------|------------|
| 1 | Foundation | software-architecture |
| 2 | Core Domain | reliability, data-persistence, networking-api |
| 3 | Cross-Cutting | security, ui-ux-design, accessibility, localization-i18n, testing-qa, devops-observability, code-quality, development-process, claude-code |
| 4 | Platform | platform-ios-apple, platform-android, platform-windows, platform-web-frontend, platform-web-backend, platform-database |
```

- [ ] **Step 2:** Create `research/specialist-assignment.json`

```json
{
  "category-mappings": {
    "recipe.ui": ["ui-ux-design", "accessibility"],
    "recipe.infrastructure": ["software-architecture", "code-quality"],
    "recipe.app": ["software-architecture", "development-process"]
  },
  "content-keywords": {
    "auth": "security",
    "tokens": "security",
    "credentials": "security",
    "network": "networking-api",
    "API": "networking-api",
    "endpoint": "networking-api",
    "HTTP": "networking-api",
    "storage": "data-persistence",
    "persistence": "data-persistence",
    "database": "data-persistence",
    "cache": "data-persistence",
    "logging": "devops-observability",
    "analytics": "devops-observability",
    "monitoring": "devops-observability",
    "localization": "localization-i18n",
    "i18n": "localization-i18n",
    "RTL": "localization-i18n",
    "test": "testing-qa",
    "testing": "testing-qa",
    "claude": "claude-code",
    "skill": "claude-code",
    "rule": "claude-code",
    "agent": "claude-code",
    "hook": "claude-code",
    "MCP": "claude-code"
  },
  "platform-mappings": {
    "ios": ["platform-ios-apple"],
    "macos": ["platform-ios-apple"],
    "android": ["platform-android"],
    "windows": ["platform-windows"],
    "web": ["platform-web-frontend", "platform-web-backend"]
  },
  "tier-order": [
    "software-architecture",
    "reliability",
    "data-persistence",
    "networking-api",
    "security",
    "ui-ux-design",
    "accessibility",
    "localization-i18n",
    "testing-qa",
    "devops-observability",
    "code-quality",
    "development-process",
    "claude-code",
    "platform-ios-apple",
    "platform-android",
    "platform-windows",
    "platform-web-frontend",
    "platform-web-backend",
    "platform-database"
  ]
}
```

- [ ] **Step 3:** Create `scripts/assign-specialists.sh`

```bash
#!/bin/bash
# assign-specialists.sh — Determine specialist assignment for a recipe
# Usage: assign-specialists.sh <recipe-path> [--platforms '<json-array>'] [--tier-order]
# Outputs: Newline-separated specialist domains to stdout
# With --tier-order: output is sorted by build tier

set -euo pipefail

RECIPE_PATH="$1"; shift
PLATFORMS_JSON="[]"
TIER_ORDER=false
MAPPING="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/research/specialist-assignment.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms) PLATFORMS_JSON="$2"; shift 2 ;;
    --tier-order) TIER_ORDER=true; shift ;;
    *) shift ;;
  esac
done

SPECIALISTS=()

# 1. Category mapping — extract category from recipe scope in frontmatter
RECIPE_DOMAIN=$(awk '/^---$/{ if (++n==2) exit } /^domain: / && n==1 { sub(/^domain: .*recipes\//, ""); sub(/\/[^\/]*$/, ""); gsub(/\//, "."); print }' "$RECIPE_PATH")

if [[ -n "$RECIPE_DOMAIN" ]]; then
  # Try exact match first, then prefix
  CATEGORY=$(echo "$RECIPE_DOMAIN" | cut -d. -f1-2)
  CATEGORY_PREFIX="recipe.${CATEGORY%%.*}"
  
  CATEGORY_SPECIALISTS=$(jq -r --arg cat "recipe.$CATEGORY" '
    .["category-mappings"] | to_entries[] | 
    select(.key == $cat or ($cat | startswith(.key))) | 
    .value[]' "$MAPPING" 2>/dev/null || true)
  
  for s in $CATEGORY_SPECIALISTS; do
    SPECIALISTS+=("$s")
  done
fi

# 2. Content keyword scan
RECIPE_CONTENT=$(cat "$RECIPE_PATH")
KEYWORD_SPECIALISTS=$(jq -r '.["content-keywords"] | to_entries[] | .key' "$MAPPING")

for keyword in $KEYWORD_SPECIALISTS; do
  if echo "$RECIPE_CONTENT" | grep -qi "$keyword"; then
    SPECIALIST=$(jq -r --arg kw "$keyword" '.["content-keywords"][$kw]' "$MAPPING")
    SPECIALISTS+=("$SPECIALIST")
  fi
done

# 3. Platform specialists
PLATFORM_SPECIALISTS=$(echo "$PLATFORMS_JSON" | jq -r '.[]' | while read -r plat; do
  jq -r --arg p "$plat" '.["platform-mappings"][$p] // [] | .[]' "$MAPPING"
done)

for s in $PLATFORM_SPECIALISTS; do
  SPECIALISTS+=("$s")
done

# Deduplicate
UNIQUE=$(printf '%s\n' "${SPECIALISTS[@]}" | sort -u)

# Apply tier ordering if requested
if $TIER_ORDER; then
  echo "$UNIQUE" | while read -r spec; do
    INDEX=$(jq -r --arg s "$spec" '.["tier-order"] | to_entries[] | select(.value == $s) | .key' "$MAPPING")
    echo "${INDEX:-999} $spec"
  done | sort -n | awk '{print $2}'
else
  echo "$UNIQUE"
fi
```

- [ ] **Step 4:** Make executable and commit

```bash
chmod +x scripts/assign-specialists.sh
git add research/specialist-assignment.md research/specialist-assignment.json scripts/assign-specialists.sh
git commit -m "Add specialist assignment reference files and shell script

Single source of truth for specialist-to-recipe mapping, replacing
duplicated logic in generate, build, and lint skills."
git push
```

---

## Task 3: Consolidate test mode spec as reference

**Files:**
- Modify: `tests/test-mode-spec.md` — ensure it's the complete, authoritative test mode reference

- [ ] **Step 1:** Read `tests/test-mode-spec.md` to see current content
- [ ] **Step 2:** Read the test mode sections from all 5 skills to identify any content in skills that isn't in the spec
- [ ] **Step 3:** If the spec is missing anything, add it. The spec must cover:
  - `--test-mode` flag detection
  - Auto-approve behavior (proceed with first/default option for all AskUserQuestion prompts)
  - `--target <path>` requirement
  - Config must pre-exist (no interactive creation)
  - No profile updates
  - Test log format: `test-log.jsonl` with unified schema
  - Test log entry schema (timestamp, event, data fields)
  - Per-skill specific test mode behaviors (if any)
- [ ] **Step 4:** Commit and push

```bash
git add tests/test-mode-spec.md
git commit -m "Consolidate test mode spec as single authoritative reference

All skills will reference this file instead of inlining test mode details."
git push
```

---

## Task 4: Update all 5 skills to use scripts and references

This is the main optimization task. Each skill gets the same treatment:
1. Replace config loading boilerplate with script call
2. Replace version check boilerplate with script call
3. Replace inlined test mode spec with reference pointer
4. (For generate/build/lint) Replace inlined specialist assignment with reference pointer

**Files:**
- Modify: `skills/interview/SKILL.md`
- Modify: `skills/create-project-from-code/SKILL.md`
- Modify: `skills/generate/SKILL.md`
- Modify: `skills/build/SKILL.md`
- Modify: `skills/lint/SKILL.md`

- [ ] **Step 1:** Read all 5 skill files to understand current structure

- [ ] **Step 2:** Update `skills/interview/SKILL.md`:

Replace the **Startup** section's version check with:
```markdown
## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `interview v0.1.0` and stop.

Otherwise, print `interview v0.1.0` as the first line of output, then proceed.

**Version check**: Run `${CLAUDE_PLUGIN_ROOT}/scripts/version-check.sh "${CLAUDE_SKILL_DIR}" "0.1.0"`. If it outputs a warning, print it and continue.
```

Replace the **Configuration** section with:
```markdown
## Configuration

Run `${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh` with `--config <path>` if `$ARGUMENTS` contains that flag. If the script fails (exit code 1), the error message tells the user what's wrong.

Extract `cookbook_repo`, `workspace_repo`, and `user_name` from the JSON output.

If config doesn't exist: "I need a config file. Create `~/.agentic-cookbook/dev-team/config.json` with `workspace_repo`, `cookbook_repo`, and `user_name` fields."
```

Replace the **Test Mode** section with:
```markdown
## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract in `${CLAUDE_PLUGIN_ROOT}/tests/test-mode-spec.md`.
```

- [ ] **Step 3:** Apply the same config/version/test-mode replacements to `skills/create-recipe-from-code/SKILL.md`

- [ ] **Step 4:** Update `skills/generate/SKILL.md` — same config/version/test-mode replacements, PLUS replace the specialist assignment section:

Replace the ~43-line inlined assignment logic in Phase 2 with:
```markdown
## Phase 2 — Specialist Assignment

Read the specialist assignment rules at `${CLAUDE_PLUGIN_ROOT}/research/specialist-assignment.md`.

For each recipe, determine relevant specialists. You can use the shell script for quick assignment:

```
${CLAUDE_PLUGIN_ROOT}/scripts/assign-specialists.sh <recipe-path> --platforms '<platforms-json>'
```

Or read `research/specialist-assignment.json` directly and apply the category, content, and platform mappings.

Limit to 3-4 specialists per recipe. Present the assignment matrix to the user and wait for approval.
```

- [ ] **Step 5:** Update `skills/build/SKILL.md` — same as generate, but add `--tier-order` flag:

```markdown
## Phase 2 — Specialist Assignment & Ordering

Read the specialist assignment rules at `${CLAUDE_PLUGIN_ROOT}/research/specialist-assignment.md`.

For each recipe, determine and order specialists by tier:

```
${CLAUDE_PLUGIN_ROOT}/scripts/assign-specialists.sh <recipe-path> --platforms '<platforms-json>' --tier-order
```

The `--tier-order` flag sorts specialists by build tier (foundation → core → cross-cutting → platform).

Limit to 3-4 specialists per recipe. Present the assignment matrix with execution order and wait for approval.
```

- [ ] **Step 6:** Update `skills/lint/SKILL.md` — same config/version/test-mode/assignment replacements as generate

- [ ] **Step 7:** Commit and push

```bash
git add skills/
git commit -m "Optimize all skills: shell scripts, reference files, progressive disclosure

- Config loading: script replaces 8-line boilerplate in each of 5 skills
- Version check: script replaces 5-line boilerplate in each of 5 skills
- Specialist assignment: reference file replaces 40-50 lines in 3 skills
- Test mode: reference pointer replaces 30-40 lines in each of 5 skills
Total: ~330 lines of duplication eliminated"
git push
```

---

## Task 5: Update CLAUDE.md and specialist guide

**Files:**
- Modify: `.claude/CLAUDE.md` — add scripts/ to repository structure
- Modify: `research/specialists/specialist-guide.md` — reference the assignment rules

- [ ] **Step 1:** Update CLAUDE.md repository structure to include:
```
scripts/                   # Shell scripts for deterministic operations
```

- [ ] **Step 2:** Update specialist-guide.md to reference `research/specialist-assignment.md` in the section about how specialists are assigned to workflows

- [ ] **Step 3:** Commit and push

```bash
git add .claude/CLAUDE.md research/specialists/specialist-guide.md
git commit -m "Document scripts/ directory and specialist assignment reference"
git push
```

---

## Verification

1. **Config script works:**
   ```bash
   scripts/load-config.sh
   # Should output JSON config to stdout
   ```

2. **Version check works:**
   ```bash
   scripts/version-check.sh skills/interview 0.1.0
   # Should output nothing (versions match) or a warning (mismatch)
   ```

3. **Specialist assignment works:**
   ```bash
   scripts/assign-specialists.sh /path/to/some/recipe.md --platforms '["ios"]'
   # Should output specialist domains, one per line
   
   scripts/assign-specialists.sh /path/to/some/recipe.md --platforms '["ios"]' --tier-order
   # Should output same specialists, sorted by tier
   ```

4. **Skills still invoke correctly:**
   - Run `/dev-team interview` — should load config via script, print version
   - Run `/dev-team lint <path>` — should assign specialists via reference/script
   - Run `/dev-team generate <path>` — should assign specialists via reference/script

5. **No duplicated logic remains:**
   ```bash
   grep -r "interview_repo" skills/  # Should find nothing (migration logic in script only)
   grep -r "~/.agentic-interviewer" skills/  # Should find nothing (migration in script only)
   ```

6. **Line count reduction:**
   ```bash
   # Before: count total skill lines
   wc -l skills/*/SKILL.md
   # After: should be ~300-330 lines fewer
   ```
