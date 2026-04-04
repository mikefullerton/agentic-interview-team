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
        manifest_lines="${manifest_lines}- specialty-teams/${specialist_name}/${team_name}.md
"
    done

    # Find the line number of ## Specialty Teams
    st_line=$(grep -n "^## Specialty Teams" "$specialist_file" | cut -d: -f1)

    # Find the next ## heading after Specialty Teams (or EOF)
    after_line=$(awk -v st="$st_line" 'NR > st && /^## / {print NR; exit}' "$specialist_file")

    # Get content before ## Specialty Teams (excluding the heading itself)
    before=$(head -n "$((st_line - 1))" "$specialist_file")

    # Get content after the Specialty Teams section (if any)
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
        printf "%s" "$manifest_lines"
        if [[ -n "$after" ]]; then
            echo ""
            echo "$after"
        fi
    } > "$specialist_file"

    team_count=$(find "$category_dir" -name '*.md' | wc -l | tr -d ' ')
    echo "OK: $specialist_name — manifest with $team_count team references"
done
