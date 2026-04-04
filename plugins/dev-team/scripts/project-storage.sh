#!/bin/bash
# project-storage.sh — Unified project management storage API
# Usage: project-storage.sh <resource> <action> [--flags...]
# Backend selected by PROJECT_STORAGE_BACKEND env var (default: markdown)
set -euo pipefail

BACKEND="${PROJECT_STORAGE_BACKEND:-markdown}"
RESOURCE="${1:?Usage: project-storage.sh <resource> <action> [flags]}"
ACTION="${2:?Usage: project-storage.sh <resource> <action> [flags]}"
shift 2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)/project-storage/${BACKEND}"

if [[ ! -d "$SCRIPT_DIR" ]]; then
  echo "Unknown backend: ${BACKEND}" >&2
  exit 1
fi

# Map hyphenated resource names to Python module names
PY_RESOURCE="${RESOURCE//-/_}"
PY_HANDLER="${SCRIPT_DIR}/${PY_RESOURCE}.py"

if [[ -x "$PY_HANDLER" ]]; then
  exec python3 "$PY_HANDLER" "$ACTION" "$@"
fi

# Fallback to shell handler
HANDLER="${SCRIPT_DIR}/${RESOURCE}.sh"

if [[ ! -x "$HANDLER" ]]; then
  echo "Unknown resource: ${RESOURCE}" >&2
  exit 1
fi

exec "$HANDLER" "$ACTION" "$@"
