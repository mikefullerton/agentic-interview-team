#!/bin/bash
# db-cleanup.sh — Age out old workflow runs and associated data
# Usage: db-cleanup.sh --older-than <duration>   e.g. 90d, 6m, 1y
#
# Cascading delete order:
#   messages → artifacts → findings (via agent_runs) → agent_runs → workflow_runs
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

# Collect IDs of workflow runs to delete
STALE_RUNS=$(sqlite3 "$DB_PATH" \
  "SELECT id FROM workflow_runs WHERE started < ${CUTOFF}")

if [[ -z "$STALE_RUNS" ]]; then
  echo '{"deleted":{"messages":0,"artifacts":0,"findings":0,"agent_runs":0,"workflow_runs":0}}'
  exit 0
fi

# Build an IN(...) clause from the stale run IDs
RUN_IDS=$(echo "$STALE_RUNS" | paste -sd ',' -)

# Collect agent_run IDs belonging to those workflow runs
STALE_AGENT_RUNS=$(sqlite3 "$DB_PATH" \
  "SELECT id FROM agent_runs WHERE workflow_run_id IN (${RUN_IDS})" || echo "")
AGENT_IDS=""
if [[ -n "$STALE_AGENT_RUNS" ]]; then
  AGENT_IDS=$(echo "$STALE_AGENT_RUNS" | paste -sd ',' -)
fi

# Count before deleting
MSG_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM messages WHERE workflow_run_id IN (${RUN_IDS})")
ART_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM artifacts WHERE workflow_run_id IN (${RUN_IDS})")

FIND_COUNT=0
AR_COUNT=0
if [[ -n "$AGENT_IDS" ]]; then
  FIND_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM findings WHERE agent_run_id IN (${AGENT_IDS})")
  AR_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM agent_runs WHERE id IN (${AGENT_IDS})")
fi

RUN_COUNT=$(sqlite3 "$DB_PATH" \
  "SELECT COUNT(*) FROM workflow_runs WHERE id IN (${RUN_IDS})")

# Cascading deletes
sqlite3 "$DB_PATH" <<SQL
DELETE FROM messages  WHERE workflow_run_id IN (${RUN_IDS});
DELETE FROM artifacts WHERE workflow_run_id IN (${RUN_IDS});
$(if [[ -n "$AGENT_IDS" ]]; then
  echo "DELETE FROM findings   WHERE agent_run_id IN (${AGENT_IDS});"
  echo "DELETE FROM agent_runs WHERE id           IN (${AGENT_IDS});"
fi)
DELETE FROM workflow_runs WHERE id IN (${RUN_IDS});
SQL

cat <<JSON
{"deleted":{"messages":${MSG_COUNT},"artifacts":${ART_COUNT},"findings":${FIND_COUNT},"agent_runs":${AR_COUNT},"workflow_runs":${RUN_COUNT}}}
JSON
