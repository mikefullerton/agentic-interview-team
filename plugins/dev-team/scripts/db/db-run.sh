#!/bin/bash
# db-run.sh — Start or complete a workflow run
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
RUN_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    --id) RUN_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --get) RUN_ID="$2"; ACTION="get"; shift 2 ;;
    --latest) ACTION="latest"; shift ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    sqlite3 "$DB_PATH" "INSERT INTO workflow_runs (project_id, workflow) VALUES ($PROJECT_ID, '$WORKFLOW'); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    sqlite3 "$DB_PATH" "UPDATE workflow_runs SET status='$STATUS', completed=CURRENT_TIMESTAMP WHERE id=$RUN_ID"
    echo "{\"id\": $RUN_ID, \"status\": \"$STATUS\"}"
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM workflow_runs WHERE id=$RUN_ID"
    ;;
  latest)
    sqlite3 -json "$DB_PATH" "SELECT * FROM workflow_runs WHERE project_id=$PROJECT_ID AND workflow='$WORKFLOW' ORDER BY started DESC LIMIT 1"
    ;;
  *)
    echo "Usage: db-run.sh start|complete|--get|--latest [options]" >&2
    exit 1
    ;;
esac
