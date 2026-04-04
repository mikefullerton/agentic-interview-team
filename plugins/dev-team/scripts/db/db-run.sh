#!/bin/bash
# db-run.sh — Start or complete a session
# Usage: db-run.sh start --project <id> --workflow <name>
#        db-run.sh complete --id <id> --status <completed|failed|interrupted>
#        db-run.sh --get <id>
#        db-run.sh --latest --project <id> --workflow <name>

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="${1:-}"; shift || true
PROJECT_ID=""
WORKFLOW=""
SESSION_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    --id) SESSION_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --get) SESSION_ID="$2"; ACTION="get"; shift 2 ;;
    --latest) ACTION="latest"; shift ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    sqlite3 "$DB_PATH" "INSERT INTO sessions (project_id, workflow) VALUES ($PROJECT_ID, '$WORKFLOW'); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    sqlite3 "$DB_PATH" "UPDATE sessions SET status='$STATUS', completed=CURRENT_TIMESTAMP WHERE id=$SESSION_ID"
    echo "{\"id\": $SESSION_ID, \"status\": \"$STATUS\"}"
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM sessions WHERE id=$SESSION_ID"
    ;;
  latest)
    sqlite3 -json "$DB_PATH" "SELECT * FROM sessions WHERE project_id=$PROJECT_ID AND workflow='$WORKFLOW' ORDER BY started DESC LIMIT 1"
    ;;
  *)
    echo "Usage: db-run.sh start|complete|--get|--latest [options]" >&2
    exit 1
    ;;
esac
