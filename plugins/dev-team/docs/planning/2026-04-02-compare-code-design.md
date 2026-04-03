# compare-code Subcommand Design Spec

## Summary

A new `/dev-team compare-code` subcommand that performs asymmetric comparison of two native code projects. Primary use case: round-trip verification (code → cookbook-project → code). Three comparison layers: structural, behavioral, and screenshot. Defaults to subset direction — "is everything in the original preserved in the regenerated version?"

## Command

```
/dev-team compare-code <baseline> <target> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<baseline>` | Yes | Path to the "original" / "less stuff" codebase |
| `<target>` | Yes | Path to the "regenerated" / "more stuff" codebase |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--direction subset\|superset\|exact` | `subset` | Comparison direction. `subset`: verify baseline is preserved in target. `superset`: verify target has no less than baseline. `exact`: strict bidirectional. |
| `--recipe <path>` | none | Cookbook recipe for behavioral comparison (maps MUST requirements to code) |
| `--screenshots` | off | Enable screenshot comparison (builds and launches macOS apps) |
| `--no-swiftui` | off | Passed through to screenshot capture if apps use AppKit |
| `--output <path>` | `./comparison-report/` | Where to write the comparison report |

## Three-Layer Comparison

### Layer 1 — Structural (fast, deterministic)

- File inventory: list all source files in both projects, match by name/path
- For each matched file: extract classes, structs, protocols/interfaces, enums, public methods, public properties
- Report:
  - Files only in baseline (missing from target — potential regression)
  - Files only in target (new — expected from cookbook additions)
  - Matched files with structural diffs (missing/added symbols)
- In `subset` direction: every class/protocol/method in baseline MUST have a counterpart in target. Target can have more.
- Implementation: shell scripts + grep — no model tokens needed for symbol extraction

### Layer 2 — Behavioral (requires --recipe, model-assisted)

- Only runs if `--recipe` is provided
- Read the recipe, extract all MUST/SHOULD requirements
- For each requirement, search both codebases for implementation evidence
- Report:
  - Requirements covered by both (preserved)
  - Requirements covered only by target (expected — cookbook guideline additions)
  - Requirements covered only by baseline (unexpected — regression)
  - Requirements covered by neither (gap in both)
- Implementation: uses the artifact-reviewer agent pattern — specialist evaluation of each codebase against the recipe

### Layer 3 — Line-level diff (detailed, filterable)

- For each matched file pair, produce a filtered diff
- Filter out: whitespace changes, import ordering, comments, auto-generated headers
- Highlight: logic changes, API signature changes, missing code blocks
- In `subset` direction: flag lines/blocks present in baseline but absent from target (potential regressions)
- Implementation: `diff` with smart filtering via shell script, model interprets significant differences

## Screenshot Comparison

Only runs when `--screenshots` is passed. macOS-focused.

### Process

1. Build both apps (`swift build` or build command from scaffold report)
2. Launch baseline app, wait for main window to appear
3. Capture screenshots at defined points:
   - **Launch state** — main window on first run
   - **Each menu command** — activate each menu item and capture
   - **Each window type** — open settings, document, etc. if defined in recipe
4. Quit baseline app, launch target app, repeat same capture sequence
5. Compare screenshot pairs:
   - **Pixel diff** — ImageMagick `compare`, produce diff image
   - **Perceptual diff** — calculate similarity percentage
   - **Report** — side-by-side pairs with diff overlay and similarity score

### Limitations (v1)

- macOS only — uses `screencapture` CLI and `open` to launch `.app` bundles
- Apps must be buildable and launchable without signing/entitlements
- Navigation is best-effort — menu commands and known window types, not deep interaction
- No iOS Simulator support yet

### Fallback

If build or launch fails for either project, skip screenshots and report the failure. Do not block the code comparison layers.

## Output Report

```
<output>/
  comparison-report.md          # Main report with all three layers
  structural/
    file-inventory.md           # Side-by-side file listing
    structural-diff.md          # Classes/protocols/methods comparison
  behavioral/
    requirement-coverage.md     # Per-requirement coverage matrix (if --recipe)
  screenshots/
    baseline/                   # Captured screenshots from baseline app
    target/                     # Captured screenshots from target app
    diffs/                      # Diff overlay images
    screenshot-comparison.md    # Side-by-side report with similarity scores
  line-level/
    <filename>.diff             # Filtered diff per matched file
```

### Main Report Structure

1. **Summary** — overall verdict, counts per layer
2. **Structural** — missing files, missing APIs, new additions
3. **Behavioral** — requirement coverage matrix (if recipe provided)
4. **Screenshots** — similarity scores, flagged differences (if --screenshots)
5. **Line-level** — significant diffs grouped by severity (regressions first, then changes, then additions)
6. **Verdict** — "Round-trip preserved N% of baseline" with specific gaps listed

## Agent Orchestration

### New Agent: code-comparator

- Purpose: Structural comparison (Layer 1) and line-level diff (Layer 3)
- Tools: Read, Glob, Grep, Bash
- Input: baseline path, target path, direction, file filter
- Output: structural inventory + filtered diffs
- Mostly shell-script driven — extract symbols with grep/awk, diff with filters

### Reused: artifact-reviewer

- Purpose: Behavioral comparison (Layer 2) — already knows how to map recipe requirements to code
- Spawned once per project (baseline and target), results compared by the meeting leader

### New Script: capture-screenshots.sh

- `scripts/capture-screenshots.sh <app-path> <output-dir>`
- Builds the app, launches it, uses `screencapture` to capture windows
- Deterministic — no model tokens
- Screenshot comparison uses ImageMagick `compare`

### Workflow Sequence

1. Spawn code-comparator agent for Layer 1 (structural)
2. If `--recipe`: spawn artifact-reviewer on both codebases for Layer 2 (behavioral)
3. Spawn code-comparator agent for Layer 3 (line-level, reuses Layer 1 file matching)
4. If `--screenshots`: run capture script on both apps, run comparison script
5. Compile all results into unified report

## Integration

- New workflow file: `skills/dev-team/workflows/compare-code.md`
- New agent: `agents/code-comparator.md`
- New script: `scripts/capture-screenshots.sh`
- Router update: add `compare-code` subcommand to routing table and help text
- Version bump: router to 0.4.0 (new subcommand = minor version)
