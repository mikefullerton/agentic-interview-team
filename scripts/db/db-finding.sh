#!/bin/bash
# db-finding.sh — Record or update a finding
# Usage: db-finding.sh --agent-run <id> --project <id> --type <type> --severity <sev> --description "<text>" [--artifact-path <path>]
#        db-finding.sh update --id <id> --status <accepted|rejected|fixed>
#        db-finding.sh --list --project <id> [--type <type>] [--status <status>]

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="create"
AGENT_RUN_ID=""
PROJECT_ID=""
TYPE=""
SEVERITY=""
DESCRIPTION=""
ARTIFACT_PATH=""
FINDING_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    update) ACTION="update"; shift ;;
    --list) ACTION="list"; shift ;;
    --agent-run) AGENT_RUN_ID="$2"; shift 2 ;;
    --project) PROJECT_ID="$2"; shift 2 ;;
    --type) TYPE="$2"; shift 2 ;;
    --severity) SEVERITY="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    --artifact-path) ARTIFACT_PATH="$2"; shift 2 ;;
    --id) FINDING_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  create)
    AR_VAL="NULL"; [[ -n "$AGENT_RUN_ID" ]] && AR_VAL="$AGENT_RUN_ID"
    SEV_VAL="NULL"; [[ -n "$SEVERITY" ]] && SEV_VAL="'$SEVERITY'"
    AP_VAL="NULL"; [[ -n "$ARTIFACT_PATH" ]] && AP_VAL="'${ARTIFACT_PATH//\'/\'\'}'"
    sqlite3 "$DB_PATH" "INSERT INTO findings (agent_run_id, project_id, type, severity, description, artifact_path) VALUES ($AR_VAL, $PROJECT_ID, '$TYPE', $SEV_VAL, '${DESCRIPTION//\'/\'\'}', $AP_VAL); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    ;;
  update)
    sqlite3 "$DB_PATH" "UPDATE findings SET status='$STATUS' WHERE id=$FINDING_ID"
    echo "{\"id\": $FINDING_ID, \"status\": \"$STATUS\"}"
    ;;
  list)
    WHERE="project_id=$PROJECT_ID"
    [[ -n "$TYPE" ]] && WHERE="$WHERE AND type='$TYPE'"
    [[ -n "$STATUS" ]] && WHERE="$WHERE AND status='$STATUS'"
    sqlite3 -json "$DB_PATH" "SELECT * FROM findings WHERE $WHERE ORDER BY created DESC"
    ;;
  *)
    echo "Usage: db-finding.sh [create|update|--list] [options]" >&2
    exit 1
    ;;
esac
