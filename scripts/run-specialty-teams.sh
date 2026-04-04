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

        # Skip empty lines
        if [[ -z "$line" ]]; then
            continue
        fi

        # Only capture first non-empty line per section
        case "$current_section" in
            focus)
                if [[ -z "$worker_focus" ]]; then
                    worker_focus="$line"
                fi
                ;;
            verify)
                if [[ -z "$verify" ]]; then
                    verify="$line"
                fi
                ;;
        esac
    done < "$team_file"

    if ! $first; then echo ","; fi
    printf '  {"name": "%s", "artifact": "%s", "worker_focus": "%s", "verify": "%s"}' \
        "$(json_escape "$name")" "$(json_escape "$artifact")" "$(json_escape "$worker_focus")" "$(json_escape "$verify")"
    first=false
done

echo ""
echo "]"
