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
