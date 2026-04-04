#!/bin/bash
# db-message.sh — Log an agent activity message
# Usage: db-message.sh --run <id> [--session-state <id>] [--agent-type <type>]
#                       [--specialist <domain>] [--persona <name>] --message "<text>"

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

SESSION_ID=""
SESSION_STATE_ID=""
AGENT_TYPE=""
SPECIALIST=""
PERSONA=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run)           SESSION_ID="$2";       shift 2 ;;
    --session-state) SESSION_STATE_ID="$2"; shift 2 ;;
    --agent-type)    AGENT_TYPE="$2";       shift 2 ;;
    --specialist)    SPECIALIST="$2";       shift 2 ;;
    --persona)       PERSONA="$2";          shift 2 ;;
    --message)       MESSAGE="$2";          shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$SESSION_ID" ]]; then
  echo "Error: --run <id> is required" >&2
  exit 1
fi

if [[ -z "$MESSAGE" ]]; then
  echo "Error: --message <text> is required" >&2
  exit 1
fi

SS_VAL="NULL";  [[ -n "$SESSION_STATE_ID" ]] && SS_VAL="$SESSION_STATE_ID"
AT_VAL="NULL";  [[ -n "$AGENT_TYPE"       ]] && AT_VAL="'${AGENT_TYPE//\'/\'\'}'"
SP_VAL="NULL";  [[ -n "$SPECIALIST"       ]] && SP_VAL="'${SPECIALIST//\'/\'\'}'"
PE_VAL="NULL";  [[ -n "$PERSONA"          ]] && PE_VAL="'${PERSONA//\'/\'\'}'"

sqlite3 "$DB_PATH" \
  "INSERT INTO messages (session_id, session_state_id, agent_type, specialist_domain, persona, message)
   VALUES ($SESSION_ID, $SS_VAL, $AT_VAL, $SP_VAL, $PE_VAL, '${MESSAGE//\'/\'\'}');
   SELECT last_insert_rowid();" \
  | tail -1 | awk '{print "{\"id\": "$1"}"}'
