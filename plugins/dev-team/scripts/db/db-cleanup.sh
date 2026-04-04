#!/bin/bash
# db-cleanup.sh — Age out old sessions and associated data
# Usage: db-cleanup.sh --older-than <duration>   e.g. 90d, 6m, 1y
#
# Cascading delete order:
#   messages → artifacts → findings (via session_state) → session_state → sessions
# Does NOT delete projects.

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

OLDER_THAN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --older-than) OLDER_THAN="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$OLDER_THAN" ]]; then
  echo "Error: --older-than <duration> is required (e.g. 90d, 6m, 1y)" >&2
  exit 1
fi

# Parse duration into SQLite modifier string
UNIT="${OLDER_THAN: -1}"
VALUE="${OLDER_THAN%?}"

if ! [[ "$VALUE" =~ ^[0-9]+$ ]]; then
  echo "Error: invalid duration '${OLDER_THAN}' — expected integer + unit (d/m/y)" >&2
  exit 1
fi

case "$UNIT" in
  d) MODIFIER="-${VALUE} days" ;;
  m) MODIFIER="-${VALUE} months" ;;
  y) MODIFIER="-${VALUE} years" ;;
  *)
    echo "Error: unknown unit '${UNIT}' — use d (days), m (months), or y (years)" >&2
    exit 1
    ;;
esac

CUTOFF="datetime('now', '${MODIFIER}')"

# Collect IDs of sessions to delete
STALE_RUNS=$(sqlite3 "$DB_PATH" \
  "SELECT id FROM sessions WHERE started < ${CUTOFF}")

if [[ -z "$STALE_RUNS" ]]; then
  echo '{"deleted":{"messages":0,"artifacts":0,"findings":0,"session_state":0,"sessions":0}}'
  exit 0
fi

# Build an IN(...) clause from the stale session IDs
SESSION_IDS=$(echo "$STALE_RUNS" | paste -sd ',' -)

# Collect session_state IDs belonging to those sessions
STALE_SESSION_STATES=$(sqlite3 "$DB_PATH" \
  "SELECT id FROM session_state WHERE session_id IN (${SESSION_IDS})" || echo "")
STATE_IDS=""
if [[ -n "$STALE_SESSION_STATES" ]]; then
  STATE_IDS=$(echo "$STALE_SESSION_STATES" | paste -sd ',' -)
fi

# Count before deleting
MSG_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM messages WHERE session_id IN (${SESSION_IDS})")
ART_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM artifacts WHERE session_id IN (${SESSION_IDS})")

FIND_COUNT=0
SS_COUNT=0
if [[ -n "$STATE_IDS" ]]; then
  FIND_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM findings WHERE session_state_id IN (${STATE_IDS})")
  SS_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM session_state WHERE id IN (${STATE_IDS})")
fi

SESSION_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM sessions WHERE id IN (${SESSION_IDS})")

# Cascading deletes
sqlite3 "$DB_PATH" <<SQL
DELETE FROM messages     WHERE session_id IN (${SESSION_IDS});
DELETE FROM artifacts    WHERE session_id IN (${SESSION_IDS});
$(if [[ -n "$STATE_IDS" ]]; then
  echo "DELETE FROM findings      WHERE session_state_id IN (${STATE_IDS});"
  echo "DELETE FROM session_state WHERE id               IN (${STATE_IDS});"
fi)
DELETE FROM sessions WHERE id IN (${SESSION_IDS});
SQL

cat <<JSON
{"deleted":{"messages":${MSG_COUNT},"artifacts":${ART_COUNT},"findings":${FIND_COUNT},"session_state":${SS_COUNT},"sessions":${SESSION_COUNT}}}
JSON
