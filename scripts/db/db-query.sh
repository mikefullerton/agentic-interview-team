#!/bin/bash
# db-query.sh — Run ad-hoc SQL against the dev-team database
# Usage: db-query.sh "<sql>"           — JSON output
#        db-query.sh --table "<sql>"   — formatted table output

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

TABLE_MODE=0
SQL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --table) TABLE_MODE=1; shift ;;
    *)       SQL="$1";     shift ;;
  esac
done

if [[ -z "$SQL" ]]; then
  echo "Usage: db-query.sh [--table] \"<sql>\"" >&2
  exit 1
fi

if [[ "$TABLE_MODE" -eq 1 ]]; then
  sqlite3 -header -column "$DB_PATH" "$SQL"
else
  sqlite3 -json "$DB_PATH" "$SQL"
fi
