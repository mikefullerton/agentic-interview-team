# compare-code Subcommand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/dev-team compare-code` subcommand that performs three-layer asymmetric comparison of two native code projects for round-trip verification.

**Architecture:** New workflow file + new code-comparator agent + screenshot capture script. The workflow orchestrates: Layer 1 (structural comparison via agent), Layer 2 (behavioral comparison via artifact-reviewer), Layer 3 (line-level diff via agent), and optional screenshot comparison via shell script. Router updated with new subcommand.

**Tech Stack:** Markdown agents, bash shell scripts, `diff`, `grep`, `awk` for code analysis, ImageMagick `compare` for screenshots, `screencapture` CLI for macOS window capture.

---

## File Structure

### New files

```
agents/code-comparator.md                          # Agent for structural + line-level comparison
scripts/capture-screenshots.sh                      # macOS screenshot capture and comparison
scripts/compare-screenshots.sh                      # ImageMagick pixel diff + similarity scoring
skills/dev-team/workflows/compare-code.md           # Workflow for the compare-code subcommand
```

### Modified files

```
skills/dev-team/SKILL.md                            # Add compare-code to routing table + help
.claude/CLAUDE.md                                   # Add compare-code to command table
```

---

## Task 1: Create the code-comparator agent

This agent handles Layer 1 (structural) and Layer 3 (line-level) comparison. It's shell-script-heavy — most work is grep/awk/diff, model interprets results.

**Files:**
- Create: `agents/code-comparator.md`

- [ ] **Step 1:** Create `agents/code-comparator.md` with this content:

```markdown
---
name: code-comparator
description: Compares two codebases structurally (symbols, APIs) and at the line level (filtered diffs). Use during the compare-code workflow.
tools:
  - Read
  - Glob
  - Grep
  - Bash
permissionMode: plan
maxTurns: 25
---

# Code Comparator

You compare two codebases — a baseline and a target — at the structural and line level.

## Input

You will receive:
1. **Baseline path** — the "original" codebase directory
2. **Target path** — the "regenerated" codebase directory
3. **Direction** — `subset` (default), `superset`, or `exact`
4. **Layer** — `structural`, `line-level`, or `both`
5. **Output path** — where to write comparison results
6. **File filter** (optional) — glob pattern to limit which files are compared (e.g., `*.swift`)
7. **Matched file list** (optional, for Layer 3) — reuse file matching from Layer 1

## Layer 1: Structural Comparison

### Step 1: File Inventory

List all source files in both projects, excluding build artifacts, dependencies, and generated files:

```bash
# List source files (adjust extensions for the detected language)
find <baseline> -type f \( -name "*.swift" -o -name "*.kt" -o -name "*.ts" -o -name "*.py" -o -name "*.cs" -o -name "*.rs" \) \
  -not -path "*/.build/*" -not -path "*/node_modules/*" -not -path "*/build/*" -not -path "*/.git/*" | sort

find <target> -type f \( -name "*.swift" -o -name "*.kt" -o -name "*.ts" -o -name "*.py" -o -name "*.cs" -o -name "*.rs" \) \
  -not -path "*/.build/*" -not -path "*/node_modules/*" -not -path "*/build/*" -not -path "*/.git/*" | sort
```

Match files by relative path from their project root. Categorize:
- **Matched** — same relative path in both
- **Baseline only** — exists in baseline, not in target (regression in subset/exact mode)
- **Target only** — exists in target, not in baseline (expected additions)

### Step 2: Symbol Extraction

For each matched file pair, extract public symbols using language-appropriate patterns:

**Swift:**
```bash
grep -nE '^\s*(public |open )?(class|struct|protocol|enum|func|var|let) ' <file>
```

**Kotlin:**
```bash
grep -nE '^\s*(public |open |internal )?(class|interface|enum|fun|val|var) ' <file>
```

**TypeScript:**
```bash
grep -nE '^\s*export\s+(class|interface|enum|function|const|type) ' <file>
```

Compare extracted symbols between baseline and target files:
- Symbols in baseline but not target → **missing** (regression flag in subset mode)
- Symbols in target but not baseline → **added** (expected)
- Symbols in both → **preserved**

### Step 3: Write Structural Report

Write to `<output>/structural/file-inventory.md`:

```markdown
# File Inventory

## Matched Files (<N>)
| Relative Path | Baseline Lines | Target Lines | Status |
|--------------|---------------|-------------|--------|
| <path> | <n> | <n> | preserved / modified |

## Baseline Only (<N>) — potential regressions
| Relative Path | Lines |
|--------------|-------|
| <path> | <n> |

## Target Only (<N>) — new additions
| Relative Path | Lines |
|--------------|-------|
| <path> | <n> |
```

Write to `<output>/structural/structural-diff.md`:

```markdown
# Structural Comparison

Direction: <subset|superset|exact>

## Per-File Symbol Comparison

### <relative-path>
- **Missing from target:** <list of symbols> (REGRESSION)
- **Added in target:** <list of symbols>
- **Preserved:** <count> symbols

### <next-file>
...

## Summary
- Files matched: <N>
- Files missing from target: <N>
- Files only in target: <N>
- Symbols missing from target: <N> (regressions)
- Symbols added in target: <N>
- Symbols preserved: <N>
```

## Layer 3: Line-Level Diff

### Step 1: Filtered Diff

For each matched file pair, produce a filtered diff:

```bash
# Generate diff, filter noise
diff -u <baseline-file> <target-file> \
  | grep -v '^\s*$' \
  | grep -v '^\s*//' \
  | grep -v '^\s*import ' \
  | grep -v '^\s*#' \
  > <output>/line-level/<filename>.diff
```

If the diff is empty after filtering, the files are functionally equivalent.

### Step 2: Classify Differences

For each non-empty diff file, read the diff and classify changes:
- **Regression** — code present in baseline but removed in target (lines starting with `-` that aren't comments/whitespace/imports)
- **Addition** — code present in target but not baseline (lines starting with `+` — expected from cookbook enhancements)
- **Modification** — code changed between baseline and target (adjacent `-` and `+` lines)

### Step 3: Write Line-Level Summary

Append to the output a summary of significant differences, grouped by severity:

1. **Regressions** (baseline code missing from target) — list file + line + content
2. **Modifications** (baseline code changed in target) — list file + before/after
3. **Additions** (new code in target) — count only, don't enumerate (expected to be large)

## Output

Return a summary report to the caller:

```markdown
## Code Comparator Results

### Structural (Layer 1)
- Files matched: <N>, baseline-only: <N>, target-only: <N>
- Symbols: preserved <N>, missing <N> (regressions), added <N>

### Line-Level (Layer 3)
- Files compared: <N>
- Regressions found: <N> (in <M> files)
- Modifications: <N>
- Additions: <N> files with new code

### Detailed reports written to:
- `<output>/structural/file-inventory.md`
- `<output>/structural/structural-diff.md`
- `<output>/line-level/<filename>.diff` (per file)
```

## Guidelines

- Use shell commands for all file listing, symbol extraction, and diff generation — no model tokens for deterministic operations
- Only use model reasoning to interpret ambiguous results (e.g., "is this a renamed symbol or a removed one?")
- In `subset` direction: regressions (baseline code missing from target) are the primary concern
- In `exact` direction: both regressions AND unexpected additions are flagged
- In `superset` direction: only flag if target has LESS than baseline
```

- [ ] **Step 2:** Commit and push

```bash
git add agents/code-comparator.md
git commit -m "Add code-comparator agent for structural and line-level comparison"
git push
```

---

## Task 2: Create screenshot capture scripts

**Files:**
- Create: `scripts/capture-screenshots.sh`
- Create: `scripts/compare-screenshots.sh`

- [ ] **Step 1:** Create `scripts/capture-screenshots.sh`:

```bash
#!/bin/bash
# capture-screenshots.sh — Build a macOS app, launch it, capture window screenshots
# Usage: capture-screenshots.sh <project-path> <output-dir> [--no-swiftui]
# Requires: Xcode command line tools, screencapture
# Outputs: PNG screenshots in <output-dir>/

set -euo pipefail

PROJECT_PATH="$1"
OUTPUT_DIR="$2"
NO_SWIFTUI=false

while [[ $# -gt 2 ]]; do
  case "${3:-}" in
    --no-swiftui) NO_SWIFTUI=true; shift ;;
    *) shift ;;
  esac
done

mkdir -p "$OUTPUT_DIR"

# Step 1: Build the app
echo "Building app at $PROJECT_PATH..." >&2
BUILD_DIR="$PROJECT_PATH/.build/release"

if [[ -f "$PROJECT_PATH/Package.swift" ]]; then
  cd "$PROJECT_PATH"
  swift build -c release 2>&1 | tail -5 >&2
  APP_NAME=$(swift package describe --type json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null || basename "$PROJECT_PATH")
  APP_PATH=$(find "$BUILD_DIR" -name "*.app" -maxdepth 1 2>/dev/null | head -1)
  if [[ -z "$APP_PATH" ]]; then
    # SwiftPM executable, not .app bundle
    APP_PATH="$BUILD_DIR/$APP_NAME"
  fi
elif [[ -f "$PROJECT_PATH/Makefile" ]]; then
  cd "$PROJECT_PATH"
  make release 2>&1 | tail -5 >&2
  APP_PATH=$(find . -name "*.app" -maxdepth 3 2>/dev/null | head -1)
else
  echo "Cannot determine build system for $PROJECT_PATH" >&2
  exit 1
fi

if [[ -z "$APP_PATH" || ! -e "$APP_PATH" ]]; then
  echo "Build succeeded but no app found at expected location" >&2
  exit 1
fi

# Step 2: Launch the app
echo "Launching $APP_PATH..." >&2
if [[ -d "$APP_PATH" ]]; then
  # .app bundle
  open -a "$APP_PATH" --args --screenshot-mode 2>/dev/null &
else
  # executable
  "$APP_PATH" &
fi
APP_PID=$!

# Wait for window to appear (up to 10 seconds)
for i in $(seq 1 20); do
  sleep 0.5
  WINDOW_COUNT=$(osascript -e "tell application \"System Events\" to count windows of (first process whose unix id is $APP_PID)" 2>/dev/null || echo "0")
  if [[ "$WINDOW_COUNT" -gt 0 ]]; then
    break
  fi
done

if [[ "$WINDOW_COUNT" -eq 0 ]]; then
  echo "App launched but no windows appeared after 10 seconds" >&2
  kill "$APP_PID" 2>/dev/null || true
  exit 1
fi

# Step 3: Capture main window
echo "Capturing launch state..." >&2
sleep 1  # Let rendering settle
screencapture -l "$(osascript -e "tell application \"System Events\" to get id of first window of (first process whose unix id is $APP_PID)" 2>/dev/null)" "$OUTPUT_DIR/01-launch-state.png" 2>/dev/null || \
  screencapture -w "$OUTPUT_DIR/01-launch-state.png" 2>/dev/null || \
  echo "Could not capture window screenshot" >&2

# Step 4: Capture menu items (best-effort)
SCREENSHOT_NUM=2
APP_PROCESS_NAME=$(osascript -e "tell application \"System Events\" to get name of (first process whose unix id is $APP_PID)" 2>/dev/null || echo "")

if [[ -n "$APP_PROCESS_NAME" ]]; then
  # Get menu bar items (skip Apple menu)
  MENUS=$(osascript -e "
    tell application \"System Events\"
      tell process \"$APP_PROCESS_NAME\"
        get name of every menu bar item of menu bar 1
      end tell
    end tell
  " 2>/dev/null || echo "")

  for menu in $MENUS; do
    [[ "$menu" == "Apple" ]] && continue
    # Click menu to open it
    osascript -e "
      tell application \"System Events\"
        tell process \"$APP_PROCESS_NAME\"
          click menu bar item \"$menu\" of menu bar 1
        end tell
      end tell
    " 2>/dev/null || continue
    sleep 0.5
    screencapture "$OUTPUT_DIR/$(printf '%02d' $SCREENSHOT_NUM)-menu-$menu.png" 2>/dev/null || true
    SCREENSHOT_NUM=$((SCREENSHOT_NUM + 1))
    # Press Escape to close menu
    osascript -e 'tell application "System Events" to key code 53' 2>/dev/null || true
    sleep 0.3
  done
fi

# Step 5: Quit the app
echo "Quitting app..." >&2
kill "$APP_PID" 2>/dev/null || true
wait "$APP_PID" 2>/dev/null || true

echo "Captured screenshots in $OUTPUT_DIR" >&2
ls -1 "$OUTPUT_DIR"/*.png 2>/dev/null | wc -l | xargs echo "Total screenshots:" >&2
```

- [ ] **Step 2:** Create `scripts/compare-screenshots.sh`:

```bash
#!/bin/bash
# compare-screenshots.sh — Compare two sets of screenshots using ImageMagick
# Usage: compare-screenshots.sh <baseline-dir> <target-dir> <output-dir>
# Requires: ImageMagick (compare, identify commands)
# Outputs: Diff images in <output-dir>/diffs/, report to stdout

set -euo pipefail

BASELINE_DIR="$1"
TARGET_DIR="$2"
OUTPUT_DIR="$3"

mkdir -p "$OUTPUT_DIR/diffs"

# Check for ImageMagick
if ! command -v compare &> /dev/null; then
  echo "ImageMagick not installed. Install with: brew install imagemagick" >&2
  exit 1
fi

echo "# Screenshot Comparison"
echo ""
echo "| Screenshot | Baseline | Target | Similarity | Diff |"
echo "|------------|----------|--------|------------|------|"

TOTAL=0
MATCHED=0

for BASELINE_IMG in "$BASELINE_DIR"/*.png; do
  [[ -f "$BASELINE_IMG" ]] || continue
  FILENAME=$(basename "$BASELINE_IMG")
  TARGET_IMG="$TARGET_DIR/$FILENAME"
  DIFF_IMG="$OUTPUT_DIR/diffs/diff-$FILENAME"

  TOTAL=$((TOTAL + 1))

  if [[ ! -f "$TARGET_IMG" ]]; then
    echo "| $FILENAME | exists | **missing** | N/A | N/A |"
    continue
  fi

  # Resize target to match baseline dimensions for comparison
  BASELINE_SIZE=$(identify -format "%wx%h" "$BASELINE_IMG" 2>/dev/null)

  # Calculate pixel difference
  DIFF_PIXELS=$(compare -metric AE "$BASELINE_IMG" "$TARGET_IMG" "$DIFF_IMG" 2>&1 || true)
  TOTAL_PIXELS=$(identify -format "%[fx:w*h]" "$BASELINE_IMG" 2>/dev/null || echo "1")

  if [[ "$TOTAL_PIXELS" -gt 0 && "$DIFF_PIXELS" =~ ^[0-9]+$ ]]; then
    SIMILARITY=$(python3 -c "print(f'{(1 - $DIFF_PIXELS / $TOTAL_PIXELS) * 100:.1f}%')" 2>/dev/null || echo "N/A")
  else
    SIMILARITY="N/A"
  fi

  if [[ "$DIFF_PIXELS" == "0" ]]; then
    MATCHED=$((MATCHED + 1))
    echo "| $FILENAME | exists | exists | 100.0% | identical |"
    rm -f "$DIFF_IMG"  # No diff needed for identical images
  else
    echo "| $FILENAME | exists | exists | $SIMILARITY | [diff](diffs/diff-$FILENAME) |"
  fi
done

# Check for target-only screenshots
for TARGET_IMG in "$TARGET_DIR"/*.png; do
  [[ -f "$TARGET_IMG" ]] || continue
  FILENAME=$(basename "$TARGET_IMG")
  if [[ ! -f "$BASELINE_DIR/$FILENAME" ]]; then
    echo "| $FILENAME | **missing** | exists | N/A | new in target |"
  fi
done

echo ""
echo "**Summary:** $MATCHED/$TOTAL screenshots identical"
```

- [ ] **Step 3:** Make both executable and commit

```bash
chmod +x scripts/capture-screenshots.sh scripts/compare-screenshots.sh
git add scripts/capture-screenshots.sh scripts/compare-screenshots.sh
git commit -m "Add screenshot capture and comparison scripts for macOS

capture-screenshots.sh: builds app, launches, captures windows and menus
compare-screenshots.sh: ImageMagick pixel diff with similarity scoring"
git push
```

---

## Task 3: Create the compare-code workflow

**Files:**
- Create: `skills/dev-team/workflows/compare-code.md`

- [ ] **Step 1:** Create `skills/dev-team/workflows/compare-code.md`:

```markdown
<!-- Workflow: compare-code — loaded by /dev-team router -->

# Compare Code

## Overview

You compare two native code projects — a baseline ("original") and a target ("regenerated") — to verify that a round-trip through the cookbook preserved the original's functionality. The comparison is asymmetric by default: you verify that everything in the baseline exists in the target, while the target may have more (cookbook guideline additions).

You orchestrate three comparison layers plus optional screenshot comparison:
1. **Structural** — file inventory, symbol extraction, API comparison (agent + shell)
2. **Behavioral** — recipe requirement coverage in both codebases (artifact-reviewer agent)
3. **Line-level** — filtered diffs highlighting regressions (agent + shell)
4. **Screenshots** — visual comparison of running apps (shell scripts, macOS only)

Your persona: a meticulous QA lead verifying a migration. You present findings layered from high-level (structural) to detailed (line-level), flag regressions clearly, and distinguish expected additions from unexpected removals.

## Parse Arguments

From `$ARGUMENTS` (after the `compare-code` subcommand has been stripped by the router):

- **First positional arg** → baseline path. Validate: directory exists.
- **Second positional arg** → target path. Validate: directory exists.
- `--direction <subset|superset|exact>` → comparison direction. Default: `subset`.
- `--recipe <path>` → cookbook recipe for behavioral comparison. Optional.
- `--screenshots` → enable screenshot comparison. Default: off.
- `--no-swiftui` → pass through to screenshot capture.
- `--output <path>` → report output directory. Default: `./comparison-report/`.

If baseline or target is missing, ask: "I need two project paths to compare. Usage: `/dev-team compare-code <baseline> <target>`"

Present: "Comparing **<baseline-name>** (baseline) against **<target-name>** (target). Direction: **<direction>**. Layers: structural, line-level<, behavioral (recipe: <name>)><, screenshots>."

## Phase 1 — Structural Comparison (Layer 1)

Create the output directory structure:
```bash
mkdir -p <output>/structural <output>/line-level
```

Spawn the **code-comparator** agent (`agents/code-comparator.md`) using the Agent tool with `subagent_type: "code-comparator"`:

Provide:
- **Baseline path**
- **Target path**
- **Direction**
- **Layer**: `structural`
- **Output path**: `<output>/structural/`

The agent produces file inventory and structural diff reports.

**Immediately persist** — the agent writes directly to the output path.

Present summary:
"**Structural comparison complete.**
- Files: <N> matched, <N> baseline-only (regressions), <N> target-only (additions)
- Symbols: <N> preserved, <N> missing (regressions), <N> added"

If there are regressions (baseline-only files or missing symbols), flag them:
"⚠ **<N> structural regressions found** — files or symbols in baseline missing from target. See `structural/structural-diff.md` for details."

## Phase 2 — Behavioral Comparison (Layer 2)

**Only if `--recipe` was provided.** Otherwise skip to Phase 3.

```bash
mkdir -p <output>/behavioral
```

Spawn two **artifact-reviewer** agents in parallel (`agents/artifact-reviewer.md`) using the Agent tool with `subagent_type: "artifact-reviewer"`:

**Agent A — Baseline review:**
- Artifact path: baseline directory
- Artifact type: `implementation`
- Specialist domain: determined from recipe content (use specialist assignment)
- Recipe path: the provided recipe
- Cookbook repo path from config

**Agent B — Target review:**
- Same inputs but artifact path is target directory

Both agents evaluate the implementation against recipe MUST/SHOULD requirements and return which requirements are covered.

**Compare results:**
Read both agents' outputs. For each requirement, determine:
- **Both** — requirement covered by baseline AND target (preserved)
- **Target only** — covered by target but not baseline (expected — cookbook additions)
- **Baseline only** — covered by baseline but not target (REGRESSION)
- **Neither** — not covered by either (gap)

Write to `<output>/behavioral/requirement-coverage.md`:

```markdown
# Requirement Coverage Matrix

Recipe: <recipe path>
Direction: <direction>

| Requirement | Baseline | Target | Status |
|-------------|----------|--------|--------|
| <MUST requirement text> | ✓ | ✓ | preserved |
| <MUST requirement text> | ✗ | ✓ | added (expected) |
| <MUST requirement text> | ✓ | ✗ | **REGRESSION** |
| <SHOULD requirement text> | ✗ | ✗ | gap |

## Summary
- Preserved: <N>
- Added in target: <N>
- Regressions: <N>
- Gaps: <N>
```

Present summary:
"**Behavioral comparison complete.**
- <N> requirements preserved, <N> added in target, <N> regressions, <N> gaps"

## Phase 3 — Line-Level Comparison (Layer 3)

Spawn the **code-comparator** agent again:

Provide:
- **Baseline path**
- **Target path**
- **Direction**
- **Layer**: `line-level`
- **Output path**: `<output>/line-level/`
- **Matched file list** — from the structural comparison (Phase 1) to avoid re-scanning

The agent produces filtered diffs per file and a summary.

**Immediately persist** — the agent writes diff files and summary to the output path.

Present summary:
"**Line-level comparison complete.**
- <N> files compared, <N> regressions in <M> files, <N> modifications, <N> files with additions"

## Phase 4 — Screenshot Comparison

**Only if `--screenshots` was passed.** Otherwise skip to Phase 5.

```bash
mkdir -p <output>/screenshots/baseline <output>/screenshots/target <output>/screenshots/diffs
```

### Capture baseline screenshots

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/capture-screenshots.sh <baseline-path> <output>/screenshots/baseline
```

If the script fails (exit code non-zero), report: "Could not capture baseline screenshots: <error>. Skipping screenshot comparison."

### Capture target screenshots

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/capture-screenshots.sh <target-path> <output>/screenshots/target
```

If the script fails, report and skip.

### Compare screenshots

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/compare-screenshots.sh \
  <output>/screenshots/baseline \
  <output>/screenshots/target \
  <output>/screenshots \
  > <output>/screenshots/screenshot-comparison.md
```

Present the comparison table from the script output.

## Phase 5 — Compile Report

Write `<output>/comparison-report.md`:

```markdown
# Code Comparison Report

**Baseline:** <baseline-path>
**Target:** <target-path>
**Direction:** <direction>
**Date:** <ISO 8601>

## Summary

| Layer | Result | Details |
|-------|--------|---------|
| Structural | <N> regressions / <N> preserved | <N> files matched, <N> baseline-only |
| Behavioral | <N> regressions / <N> preserved | (if --recipe, otherwise "skipped") |
| Line-level | <N> regressions in <M> files | <N> modifications, <N> additions |
| Screenshots | <N>/<M> identical | (if --screenshots, otherwise "skipped") |

## Verdict

<Based on direction:>
- subset: "Round-trip preserved **<N>%** of baseline. <M> regressions require attention."
- exact: "Codebases differ in <N> files. <M> regressions, <K> additions."
- superset: "Target covers **<N>%** of baseline functionality."

## Structural Comparison
<include or link to structural/structural-diff.md>

## Behavioral Comparison
<include or link to behavioral/requirement-coverage.md, or "Skipped — no recipe provided">

## Line-Level Comparison
<summarize significant diffs, link to line-level/ directory>

## Screenshot Comparison
<include or link to screenshots/screenshot-comparison.md, or "Skipped">

## Regressions (Action Required)
<consolidated list of all regressions across all layers, prioritized>
```

Present the verdict to the user:
"**Comparison complete.** Report at `<output>/comparison-report.md`."
"Round-trip preserved **<N>%** of baseline. **<M> regressions** require attention."

If there are regressions, list the top 5 most significant ones.

## Error Handling

- **Baseline or target doesn't exist**: Stop immediately, report which path is invalid.
- **No source files found**: Report "No source files found in <path>. Is this a valid code project?"
- **Build fails for screenshots**: Skip screenshots, report the build error, continue with code layers.
- **ImageMagick not installed**: Skip screenshot comparison, suggest `brew install imagemagick`.
- **Agent fails**: Report which layer failed, continue with remaining layers. A partial report is better than no report.

## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract in `${CLAUDE_PLUGIN_ROOT}/tests/test-mode-spec.md`.
```

- [ ] **Step 2:** Commit and push

```bash
git add skills/dev-team/workflows/compare-code.md
git commit -m "Add compare-code workflow for round-trip verification

Five phases: structural comparison, behavioral comparison (if recipe),
line-level diff, screenshot comparison (if --screenshots), compile report.
Asymmetric by default — verify baseline preserved in target."
git push
```

---

## Task 4: Update router with compare-code subcommand

**Files:**
- Modify: `skills/dev-team/SKILL.md`

- [ ] **Step 1:** Read `skills/dev-team/SKILL.md`

- [ ] **Step 2:** Add `compare-code` to the routing table:

In the routing table, add after the `lint` row:
```markdown
| `compare-code` | `${CLAUDE_SKILL_DIR}/workflows/compare-code.md` |
```

- [ ] **Step 3:** Add to the help text:

After the `lint` line in the help text, add:
```
  compare-code                   Compare two code projects (round-trip verification)
```

- [ ] **Step 4:** Update the description in frontmatter to include compare-code:

```yaml
description: Multi-agent dev team for product discovery, project creation, specialist review, building, linting, and code comparison. Subcommands: interview, create-project-from-code, generate, create-code-from-project, lint, compare-code, view-project.
```

- [ ] **Step 5:** Update argument-hint:

```yaml
argument-hint: <command> [args...] — commands: interview, create-project-from-code, generate, create-code-from-project [--no-swiftui], lint, compare-code, view-project
```

- [ ] **Step 6:** Bump version from 0.3.1 to 0.4.0 (all occurrences — frontmatter, title, startup, version-check, help text)

- [ ] **Step 7:** Commit and push

```bash
git add skills/dev-team/SKILL.md
git commit -m "Add compare-code subcommand to router

New subcommand for round-trip verification: compares baseline and target
codebases structurally, behaviorally, and visually. Router bumped to v0.4.0."
git push
```

---

## Task 5: Update CLAUDE.md with compare-code command

**Files:**
- Modify: `.claude/CLAUDE.md`

- [ ] **Step 1:** Read `.claude/CLAUDE.md`

- [ ] **Step 2:** Add `compare-code` to the command table:

After the `lint` row, add:
```markdown
| `compare-code` | Comparator | Compare two code projects for round-trip verification |
```

- [ ] **Step 3:** Update agents count if needed (we added code-comparator, so +1)

- [ ] **Step 4:** Commit and push

```bash
git add .claude/CLAUDE.md
git commit -m "Add compare-code to CLAUDE.md command table"
git push
```

---

## Verification

1. **Router recognizes compare-code:**
   ```
   /dev-team compare-code
   ```
   Expected: "I need two project paths to compare..."

2. **Help text includes compare-code:**
   ```
   /dev-team help
   ```
   Expected: `compare-code` in the command list

3. **Agent file is valid:**
   ```bash
   head -10 agents/code-comparator.md
   ```
   Expected: Valid YAML frontmatter with name, tools, maxTurns

4. **Scripts are executable:**
   ```bash
   ls -la scripts/capture-screenshots.sh scripts/compare-screenshots.sh
   ```
   Expected: `-rwxr-xr-x` permissions

5. **End-to-end test (if two projects available):**
   ```
   /dev-team compare-code /path/to/original /path/to/regenerated --direction subset
   ```
   Expected: Structural and line-level comparison report generated

6. **Screenshot test (macOS, with ImageMagick):**
   ```
   /dev-team compare-code /path/to/app1 /path/to/app2 --screenshots
   ```
   Expected: Screenshots captured and compared, or graceful error if build fails
