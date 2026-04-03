#!/bin/bash
# load-config.sh — Load and migrate dev-team configuration
# Usage: load-config.sh [--config <path>]
# Outputs: JSON config to stdout, errors to stderr
# Exit codes: 0 = success, 1 = config not found or invalid

set -euo pipefail

CONFIG_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

NEW_CONFIG="${HOME}/.agentic-cookbook/dev-team/config.json"
OLD_CONFIG="${HOME}/.agentic-interviewer/config.json"

if [[ -z "$CONFIG_PATH" ]]; then
  CONFIG_PATH="$NEW_CONFIG"
fi

# Migrate from old location if needed
if [[ ! -f "$CONFIG_PATH" && -f "$OLD_CONFIG" ]]; then
  mkdir -p "$(dirname "$CONFIG_PATH")"
  jq '{
    workspace_repo: .interview_repo,
    cookbook_repo: .cookbook_repo,
    user_name: .user_name,
    authorized_repos: (.authorized_repos // [])
  }' "$OLD_CONFIG" > "$CONFIG_PATH"
  echo "Migrated config from $OLD_CONFIG to $CONFIG_PATH" >&2
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found at $CONFIG_PATH" >&2
  exit 1
fi

# Validate required fields
if ! jq -e '.workspace_repo and .cookbook_repo and .user_name' "$CONFIG_PATH" > /dev/null 2>&1; then
  echo "Config missing required fields (workspace_repo, cookbook_repo, user_name)" >&2
  exit 1
fi

cat "$CONFIG_PATH"
