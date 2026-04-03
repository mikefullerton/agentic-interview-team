#!/bin/bash
# db-agent.sh — Start or complete an agent run
# Usage: db-agent.sh start --run <id> --agent <type> [--specialist <domain>]
#        db-agent.sh complete --id <id> --status <completed|failed> [--output-path <path>]

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="${1:-}"; shift || true
RUN_ID=""
AGENT_TYPE=""
SPECIALIST=""
AGENT_ID=""
STATUS=""
OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run) RUN_ID="$2"; shift 2 ;;
    --agent) AGENT_TYPE="$2"; shift 2 ;;
    --specialist) SPECIALIST="$2"; shift 2 ;;
    --id) AGENT_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --output-path) OUTPUT_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    SPEC_VAL="NULL"
    [[ -n "$SPECIALIST" ]] && SPEC_VAL="'$SPECIALIST'"
    sqlite3 "$DB_PATH" "INSERT INTO agent_runs (workflow_run_id, agent_type, specialist_domain) VALUES ($RUN_ID, '$AGENT_TYPE', $SPEC_VAL); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    OUT_SQL=""
    [[ -n "$OUTPUT_PATH" ]] && OUT_SQL=", output_path='${OUTPUT_PATH//\'/\'\'}'"
    sqlite3 "$DB_PATH" "UPDATE agent_runs SET status='$STATUS', completed=CURRENT_TIMESTAMP${OUT_SQL} WHERE id=$AGENT_ID"
    echo "{\"id\": $AGENT_ID, \"status\": \"$STATUS\"}"
    ;;
  *)
    echo "Usage: db-agent.sh start|complete [options]" >&2
    exit 1
    ;;
esac
