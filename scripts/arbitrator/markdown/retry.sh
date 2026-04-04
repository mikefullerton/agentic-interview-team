#!/bin/bash
# retry.sh — Retry tracking for markdown arbitrator
# Actions: create, list
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: retry.sh <create|list> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "state" "$PARSED_STATE"
    require_flag "reason" "$PARSED_REASON"

    DIR="$(require_session "$PARSED_SESSION")"
    RETRY_DIR="${DIR}/retries"
    SEQ=$(next_seq "$RETRY_DIR")
    TIMESTAMP=$(now_iso)
    TIMESTAMP_SLUG="${TIMESTAMP//:/-}"
    FILE="${RETRY_DIR}/${SEQ}-${TIMESTAMP_SLUG}.json"

    RETRY_ID="${PARSED_SESSION}:retry:${SEQ}"

    json_build \
      retry_id="$RETRY_ID" \
      session_id="$PARSED_SESSION" \
      session_state_id="$PARSED_STATE" \
      reason="$PARSED_REASON" \
      creation_date="$TIMESTAMP" \
      > "$FILE"

    json_build retry_id="$RETRY_ID"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    RETRY_DIR="${DIR}/retries"

    if [[ ! -d "$RETRY_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for f in $(find "$RETRY_DIR" -maxdepth 1 -name '*.json' 2>/dev/null | sort); do
      [[ -f "$f" ]] || continue
      RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
    done

    echo "$RESULTS"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: retry.sh <create|list> [flags]" >&2
    exit 1
    ;;
esac
