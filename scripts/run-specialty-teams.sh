#!/bin/bash
# run-specialty-teams.sh — Deterministic iterator for specialty-teams
#
# Reads a specialist manifest, extracts specialty-team definitions,
# and outputs a structured execution plan that the calling agent
# uses to spawn worker-verifier pairs one at a time.
#
# This script does NOT spawn agents itself — it parses the specialist
# file and outputs the team list as JSON for the orchestrating agent
# to iterate over deterministically.
#
# Usage:
#   run-specialty-teams.sh <specialist-file> [--mode <mode>]
#
# Output: JSON array of specialty-team definitions
#   [
#     {
#       "name": "authentication",
#       "artifact": "guidelines/security/authentication.md",
#       "worker_focus": "OAuth 2.0/OIDC with PKCE, SSO, public client flows",
#       "verify": "Auth method chosen, PKCE for public clients, no implicit flow"
#     },
#     ...
#   ]

set -euo pipefail

SPECIALIST_FILE="${1:?Usage: run-specialty-teams.sh <specialist-file> [--mode <mode>]}"
MODE="${3:-interview}"

if [[ ! -f "$SPECIALIST_FILE" ]]; then
    echo "ERROR: Specialist file not found: $SPECIALIST_FILE" >&2
    exit 1
fi

# Parse specialty teams from the specialist file
# Format expected:
#   ### <team-name>
#   - **Artifact**: `<path>`
#   - **Worker focus**: <description>
#   - **Verify**: <criteria>

in_teams=false
current_name=""
current_artifact=""
current_focus=""
current_verify=""
first=true

echo "["

while IFS= read -r line; do
    # Detect start of Specialty Teams section
    if echo "$line" | grep -q "^## Specialty Teams"; then
        in_teams=true
        continue
    fi

    # Detect end of Specialty Teams section (next ## heading)
    if $in_teams && echo "$line" | grep -q "^## " && ! echo "$line" | grep -q "^## Specialty Teams"; then
        # Flush last team
        if [[ -n "$current_name" ]]; then
            if ! $first; then echo ","; fi
            printf '  {"name": "%s", "artifact": "%s", "worker_focus": "%s", "verify": "%s"}' \
                "$current_name" "$current_artifact" "$current_focus" "$current_verify"
            first=false
        fi
        break
    fi

    if ! $in_teams; then
        continue
    fi

    # Parse team name (### heading)
    if echo "$line" | grep -q "^### "; then
        # Flush previous team
        if [[ -n "$current_name" ]]; then
            if ! $first; then echo ","; fi
            printf '  {"name": "%s", "artifact": "%s", "worker_focus": "%s", "verify": "%s"}' \
                "$current_name" "$current_artifact" "$current_focus" "$current_verify"
            first=false
        fi
        current_name=$(echo "$line" | sed 's/^### //')
        current_artifact=""
        current_focus=""
        current_verify=""
        continue
    fi

    # Parse artifact
    if echo "$line" | grep -q "^\- \*\*Artifact\*\*:"; then
        current_artifact=$(echo "$line" | sed 's/.*`\(.*\)`.*/\1/')
        continue
    fi

    # Parse worker focus
    if echo "$line" | grep -q "^\- \*\*Worker focus\*\*:"; then
        current_focus=$(echo "$line" | sed 's/.*\*\*Worker focus\*\*: //')
        continue
    fi

    # Parse verify
    if echo "$line" | grep -q "^\- \*\*Verify\*\*:"; then
        current_verify=$(echo "$line" | sed 's/.*\*\*Verify\*\*: //')
        continue
    fi

done < "$SPECIALIST_FILE"

# Flush last team if we hit EOF while in teams section
if [[ -n "$current_name" ]] && $in_teams; then
    if ! $first; then echo ","; fi
    printf '  {"name": "%s", "artifact": "%s", "worker_focus": "%s", "verify": "%s"}' \
        "$current_name" "$current_artifact" "$current_focus" "$current_verify"
fi

echo ""
echo "]"
