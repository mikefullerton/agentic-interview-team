#!/bin/bash
# reference.sh — Reference tracking for markdown arbitrator
# Actions: create, list
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: reference.sh <create|list> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "result" "$PARSED_RESULT"
    require_flag "path" "$PARSED_PATH"
    require_flag "type" "$PARSED_TYPE"

    # Parse session ID and specialist from composite result ID: <session-id>:result:<specialist>
    SESSION_ID="${PARSED_RESULT%%:result:*}"
    SPECIALIST="${PARSED_RESULT##*:result:}"

    DIR="$(require_session "$SESSION_ID")"
    REF_DIR="${DIR}/results/${SPECIALIST}/references"
    SEQ=$(next_seq "$REF_DIR")
    PATH_SLUG=$(slugify "$PARSED_PATH")
    FILE="${REF_DIR}/${SEQ}-${PARSED_TYPE}-${PATH_SLUG}.json"

    REFERENCE_ID="${PARSED_RESULT}:reference:${SEQ}"

    json_build \
      reference_id="$REFERENCE_ID" \
      result_id="$PARSED_RESULT" \
      path="$PARSED_PATH" \
      type="$PARSED_TYPE" \
      creation_date="$(now_iso)" \
      > "$FILE"

    json_build reference_id="$REFERENCE_ID"
    ;;

  list)
    require_flag "result" "$PARSED_RESULT"

    # Parse session ID and specialist from composite result ID: <session-id>:result:<specialist>
    SESSION_ID="${PARSED_RESULT%%:result:*}"
    SPECIALIST="${PARSED_RESULT##*:result:}"

    DIR="$(require_session "$SESSION_ID")"
    REF_DIR="${DIR}/results/${SPECIALIST}/references"

    if [[ ! -d "$REF_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for f in $(find "$REF_DIR" -maxdepth 1 -name '*.json' 2>/dev/null | sort); do
      [[ -f "$f" ]] || continue
      RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
    done

    echo "$RESULTS"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: reference.sh <create|list> [flags]" >&2
    exit 1
    ;;
esac
