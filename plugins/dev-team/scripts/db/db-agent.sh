#!/bin/bash
# db-agent.sh — Start or complete a state transition
# Usage: db-agent.sh start --run <id> --agent <type> [--specialist <domain>]
#        db-agent.sh complete --id <id> --status <completed|failed> [--output-path <path>]

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="${1:-}"; shift || true
SESSION_ID=""
AGENT_TYPE=""
SPECIALIST=""
SESSION_STATE_ID=""
STATUS=""
OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run) SESSION_ID="$2"; shift 2 ;;
    --agent) AGENT_TYPE="$2"; shift 2 ;;
    --specialist) SPECIALIST="$2"; shift 2 ;;
    --id) SESSION_STATE_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --output-path) OUTPUT_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    SPEC_VAL="NULL"
    [[ -n "$SPECIALIST" ]] && SPEC_VAL="'$SPECIALIST'"
    sqlite3 "$DB_PATH" "INSERT INTO session_state (session_id, agent_type, specialist_domain) VALUES ($SESSION_ID, '$AGENT_TYPE', $SPEC_VAL); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    OUT_SQL=""
    [[ -n "$OUTPUT_PATH" ]] && OUT_SQL=", output_path='${OUTPUT_PATH//\'/\'\'}'"
    sqlite3 "$DB_PATH" "UPDATE session_state SET status='$STATUS', completed=CURRENT_TIMESTAMP${OUT_SQL} WHERE id=$SESSION_STATE_ID"
    echo "{\"id\": $SESSION_STATE_ID, \"status\": \"$STATUS\"}"
    ;;
  *)
    echo "Usage: db-agent.sh start|complete [options]" >&2
    exit 1
    ;;
esac
