#!/bin/bash
# arbitrator.sh — Unified data exchange API for dev-team pipeline
# Usage: arbitrator.sh <resource> <action> [--flags...]
# Backend selected by ARBITRATOR_BACKEND env var (default: markdown)
set -euo pipefail

BACKEND="${ARBITRATOR_BACKEND:-markdown}"
RESOURCE="${1:?Usage: arbitrator.sh <resource> <action> [flags]}"
ACTION="${2:?Usage: arbitrator.sh <resource> <action> [flags]}"
shift 2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)/arbitrator/${BACKEND}"

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
