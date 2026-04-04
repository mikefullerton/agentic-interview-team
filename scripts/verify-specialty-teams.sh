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
        verify_field=$(echo "$json_line" | sed 's/.*"verify": "\([^"]*\)".*/\1/')

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
        file_focus=$(awk '/^## Worker Focus$/{found=1; next} /^## /{found=0} found' "$team_file" | sed '/^$/d')
        if [[ "$file_focus" != "$worker_focus" ]]; then
            echo "WARN: $specialist_name/$name — worker_focus differs (may be formatting)"
            echo "W" >> "$WARN_FILE"
        fi

        # Check verify in body
        file_verify=$(awk '/^## Verify$/{found=1; next} /^## /{found=0} found' "$team_file" | sed '/^$/d')
        if [[ "$file_verify" != "$verify_field" ]]; then
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
