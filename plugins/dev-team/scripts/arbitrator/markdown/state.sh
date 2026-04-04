#!/bin/bash
# state.sh — State transitions for markdown arbitrator
# Actions: append, current, list
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: state.sh <append|current|list> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  append)
    require_flag "session" "$PARSED_SESSION"
    require_flag "changed-by" "$PARSED_CHANGED_BY"
    require_flag "state" "$PARSED_STATE"

    DIR="$(require_session "$PARSED_SESSION")"
    STATE_DIR="${DIR}/state"
    SEQ=$(next_seq "$STATE_DIR")
    TIMESTAMP=$(now_iso)
    SLUG=$(slugify "$PARSED_CHANGED_BY")
    FILE="${STATE_DIR}/${SEQ}-${TIMESTAMP//:/-}-${SLUG}.json"

    ID="${PARSED_SESSION}:state:${SEQ}"

    json_build \
      id="$ID" \
      session_id="$PARSED_SESSION" \
      creation_date="$TIMESTAMP" \
      changed_by="$PARSED_CHANGED_BY" \
      state="$PARSED_STATE" \
      description="$PARSED_DESCRIPTION" \
      > "$FILE"

    cat "$FILE"
    ;;

  current)
    require_flag "session" "$PARSED_SESSION"
    require_flag "changed-by" "$PARSED_CHANGED_BY"

    DIR="$(require_session "$PARSED_SESSION")"
    STATE_DIR="${DIR}/state"

    if [[ ! -d "$STATE_DIR" ]]; then
      echo "No state found for session: ${PARSED_SESSION}" >&2
      exit 1
    fi

    SLUG=$(slugify "$PARSED_CHANGED_BY")
    LATEST=$(find "$STATE_DIR" -maxdepth 1 -name "*-${SLUG}.json" 2>/dev/null | sort | tail -1)

    if [[ -z "$LATEST" ]]; then
      echo "No state found for changed_by: ${PARSED_CHANGED_BY}" >&2
      exit 1
    fi

    cat "$LATEST"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    STATE_DIR="${DIR}/state"

    if [[ ! -d "$STATE_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for f in $(find "$STATE_DIR" -maxdepth 1 -name '*.json' 2>/dev/null | sort); do
      [[ -f "$f" ]] || continue
      RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
    done

    echo "$RESULTS"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: state.sh <append|current|list> [flags]" >&2
    exit 1
    ;;
esac
