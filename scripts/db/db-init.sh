#!/bin/bash
# db-init.sh — Create or migrate the dev-team shared database
# Usage: db-init.sh
# Idempotent — safe to call on every workflow startup

set -euo pipefail

DB_DIR="${HOME}/.agentic-cookbook/dev-team"
DB_PATH="${DB_DIR}/dev-team.db"
SCHEMA_PATH="$(dirname "$0")/schema.sql"
SCHEMA_VERSION="1"

mkdir -p "$DB_DIR"

# Apply schema (all CREATE IF NOT EXISTS — idempotent)
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"

# Check/set schema version
CURRENT_VERSION=$(sqlite3 "$DB_PATH" "SELECT value FROM meta WHERE key='schema_version'" 2>/dev/null || echo "")

if [[ -z "$CURRENT_VERSION" ]]; then
  sqlite3 "$DB_PATH" "INSERT INTO meta (key, value) VALUES ('schema_version', '$SCHEMA_VERSION')"
elif [[ "$CURRENT_VERSION" != "$SCHEMA_VERSION" ]]; then
  sqlite3 "$DB_PATH" "UPDATE meta SET value='$SCHEMA_VERSION' WHERE key='schema_version'"
  echo "Migrated database schema from v${CURRENT_VERSION} to v${SCHEMA_VERSION}" >&2
fi

echo "$DB_PATH"
