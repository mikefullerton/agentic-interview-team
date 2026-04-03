#!/bin/bash
# db-project.sh — Create or get a project
# Usage: db-project.sh --name <name> --path <path>
#        db-project.sh --get <id>
#        db-project.sh --list

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION=""
NAME=""
PROJECT_PATH=""
ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; ACTION="upsert"; shift 2 ;;
    --path) PROJECT_PATH="$2"; shift 2 ;;
    --get) ID="$2"; ACTION="get"; shift 2 ;;
    --list) ACTION="list"; shift ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  upsert)
    EXISTING=$(sqlite3 "$DB_PATH" "SELECT id FROM projects WHERE name='${NAME//\'/\'\'}' LIMIT 1" 2>/dev/null || echo "")
    if [[ -n "$EXISTING" ]]; then
      sqlite3 "$DB_PATH" "UPDATE projects SET path='${PROJECT_PATH//\'/\'\'}', modified=CURRENT_TIMESTAMP WHERE id=$EXISTING"
      echo "{\"id\": $EXISTING}"
    else
      sqlite3 "$DB_PATH" "INSERT INTO projects (name, path) VALUES ('${NAME//\'/\'\'}', '${PROJECT_PATH//\'/\'\'}'); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
    fi
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM projects WHERE id=$ID"
    ;;
  list)
    sqlite3 -json "$DB_PATH" "SELECT * FROM projects ORDER BY modified DESC"
    ;;
  *)
    echo "Usage: db-project.sh --name <name> --path <path> | --get <id> | --list" >&2
    exit 1
    ;;
esac
