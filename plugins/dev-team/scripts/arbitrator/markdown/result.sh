#!/bin/bash
# result.sh — Result resource for markdown arbitrator
# Actions: create, get, list
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: result.sh <create|get|list> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"

    DIR="$(require_session "$PARSED_SESSION")"
    RESULT_DIR="${DIR}/results/${PARSED_SPECIALIST}"
    mkdir -p "$RESULT_DIR"

    RESULT_ID="${PARSED_SESSION}:result:${PARSED_SPECIALIST}"

    json_build \
      result_id="$RESULT_ID" \
      session_id="$PARSED_SESSION" \
      specialist="$PARSED_SPECIALIST" \
      creation_date="$(now_iso)" \
      > "${RESULT_DIR}/result.json"

    json_build result_id="$RESULT_ID"
    ;;

  get)
    require_flag "result" "$PARSED_RESULT"

    # Parse composite ID: <session-id>:result:<specialist>
    SESSION_ID="${PARSED_RESULT%%:result:*}"
    SPECIALIST="${PARSED_RESULT##*:result:}"

    if [[ -z "$SESSION_ID" || -z "$SPECIALIST" || "$SESSION_ID" == "$PARSED_RESULT" ]]; then
      echo "Invalid result ID format: ${PARSED_RESULT}" >&2
      exit 1
    fi

    DIR="$(require_session "$SESSION_ID")"
    RESULT_FILE="${DIR}/results/${SPECIALIST}/result.json"

    if [[ ! -f "$RESULT_FILE" ]]; then
      echo "Result not found: ${PARSED_RESULT}" >&2
      exit 1
    fi

    cat "$RESULT_FILE"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    RESULTS_BASE="${DIR}/results"

    if [[ ! -d "$RESULTS_BASE" ]]; then
      echo "[]"
      exit 0
    fi

    OUTPUT="[]"
    for result_file in "${RESULTS_BASE}"/*/result.json; do
      [[ -f "$result_file" ]] || continue

      if [[ -n "$PARSED_SPECIALIST" ]]; then
        FILE_SPECIALIST=$(jq -r '.specialist' "$result_file")
        [[ "$FILE_SPECIALIST" == "$PARSED_SPECIALIST" ]] || continue
      fi

      OUTPUT=$(echo "$OUTPUT" | jq --argjson obj "$(cat "$result_file")" '. + [$obj]')
    done

    echo "$OUTPUT"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: result.sh <create|get|list> [flags]" >&2
    exit 1
    ;;
esac
