#!/bin/bash
# resume-session.sh — Detect interrupted sessions for a given playbook
# Usage: resume-session.sh --playbook <name>
#
# Output: JSON with interrupted session info or {"interrupted": false}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARBITRATOR="$SCRIPT_DIR/arbitrator.sh"

PLAYBOOK=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --playbook) PLAYBOOK="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$PLAYBOOK" ]]; then
  echo "Usage: resume-session.sh --playbook <name>" >&2
  exit 1
fi

# Find sessions for this playbook that were never completed or abandoned
ALL_SESSIONS=$("$ARBITRATOR" session list --playbook "$PLAYBOOK" 2>/dev/null || echo "[]")

SESSION_BASE="${ARBITRATOR_SESSION_BASE:-${HOME}/.agentic-cookbook/dev-team/sessions}"
SESSIONS="[]"
for session in $(echo "$ALL_SESSIONS" | jq -c '.[]'); do
  SESSION_ID=$(echo "$session" | jq -r '.session_id')
  SESSION_DIR="${SESSION_BASE}/${SESSION_ID}"

  if [[ -d "$SESSION_DIR/state" ]]; then
    LATEST_STATE_FILE=$(find "$SESSION_DIR/state" -name "*.json" | sort | tail -1)
    if [[ -n "$LATEST_STATE_FILE" ]]; then
      LATEST_STATE=$(jq -r '.state' "$LATEST_STATE_FILE")
      # A session is interrupted if its latest state is NOT a terminal state
      if [[ "$LATEST_STATE" != "completed" && "$LATEST_STATE" != "abandoned" ]]; then
        SESSIONS=$(echo "$SESSIONS" | jq --argjson obj "$session" '. + [$obj]')
      fi
    fi
  fi
done
SESSION_COUNT=$(echo "$SESSIONS" | jq 'length')

if [[ "$SESSION_COUNT" -eq 0 ]]; then
  echo '{"interrupted": false}'
  exit 0
fi

# Use the most recent interrupted session
SESSION=$(echo "$SESSIONS" | jq '.[-1]')
SESSION_ID=$(echo "$SESSION" | jq -r '.session_id')
CREATION_DATE=$(echo "$SESSION" | jq -r '.creation_date')

# Build specialist progress summary
RESULTS=$("$ARBITRATOR" result list --session "$SESSION_ID" 2>/dev/null || echo "[]")
SPECIALISTS="[]"

for row in $(echo "$RESULTS" | jq -c '.[]'); do
  SPECIALIST=$(echo "$row" | jq -r '.specialist')

  TEAM_RESULTS=$("$ARBITRATOR" team-result list --session "$SESSION_ID" --specialist "$SPECIALIST" 2>/dev/null || echo "[]")
  TOTAL=$(echo "$TEAM_RESULTS" | jq 'length')
  COMPLETED=$(echo "$TEAM_RESULTS" | jq '[.[] | select(.status == "passed" or .status == "escalated")] | length')
  ESCALATED=$(echo "$TEAM_RESULTS" | jq '[.[] | select(.status == "escalated")] | length')

  SPECIALISTS=$(echo "$SPECIALISTS" | jq \
    --arg name "$SPECIALIST" \
    --argjson completed "$COMPLETED" \
    --argjson total "$TOTAL" \
    --argjson escalated "$ESCALATED" \
    '. + [{"name": $name, "teams_completed": $completed, "teams_total": $total, "teams_escalated": $escalated}]')
done

jq -n \
  --argjson interrupted true \
  --arg session_id "$SESSION_ID" \
  --arg creation_date "$CREATION_DATE" \
  --argjson specialists "$SPECIALISTS" \
  '{interrupted: $interrupted, session_id: $session_id, creation_date: $creation_date, specialists: $specialists}'
