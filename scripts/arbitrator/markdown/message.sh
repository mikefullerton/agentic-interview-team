#!/bin/bash
# message.sh — Messages for markdown arbitrator
# Actions: send, list, get
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: message.sh <send|list|get> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  send)
    require_flag "session" "$PARSED_SESSION"
    require_flag "type" "$PARSED_TYPE"
    require_flag "changed-by" "$PARSED_CHANGED_BY"
    require_flag "content" "$PARSED_CONTENT"

    DIR="$(require_session "$PARSED_SESSION")"
    MSG_DIR="${DIR}/messages"
    SEQ=$(next_seq "$MSG_DIR")
    TIMESTAMP=$(now_iso)
    FILE="${MSG_DIR}/${SEQ}-${TIMESTAMP//:/-}-${PARSED_TYPE}.json"

    ID="${PARSED_SESSION}:message:${SEQ}"

    json_build \
      id="$ID" \
      session_id="$PARSED_SESSION" \
      creation_date="$TIMESTAMP" \
      type="$PARSED_TYPE" \
      changed_by="$PARSED_CHANGED_BY" \
      content="$PARSED_CONTENT" \
      specialist="$PARSED_SPECIALIST" \
      category="$PARSED_CATEGORY" \
      severity="$PARSED_SEVERITY" \
      > "$FILE"

    cat "$FILE"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    MSG_DIR="${DIR}/messages"

    if [[ ! -d "$MSG_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for f in $(find "$MSG_DIR" -maxdepth 1 -name '*.json' 2>/dev/null | sort); do
      [[ -f "$f" ]] || continue

      if [[ -n "$PARSED_TYPE" ]]; then
        FILE_TYPE=$(jq -r '.type' "$f")
        [[ "$FILE_TYPE" == "$PARSED_TYPE" ]] || continue
      fi

      RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
    done

    echo "$RESULTS"
    ;;

  get)
    require_flag "message" "$PARSED_MESSAGE"

    # Composite ID format: <session_id>:message:<seq>
    SESSION_ID="${PARSED_MESSAGE%%:message:*}"
    SEQ="${PARSED_MESSAGE##*:message:}"

    DIR="$(require_session "$SESSION_ID")"
    MSG_DIR="${DIR}/messages"

    if [[ ! -d "$MSG_DIR" ]]; then
      echo "No messages found for session: ${SESSION_ID}" >&2
      exit 1
    fi

    MATCH=$(find "$MSG_DIR" -maxdepth 1 -name "${SEQ}-*.json" 2>/dev/null | sort | head -1)

    if [[ -z "$MATCH" ]]; then
      echo "Message not found: ${PARSED_MESSAGE}" >&2
      exit 1
    fi

    cat "$MATCH"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: message.sh <send|list|get> [flags]" >&2
    exit 1
    ;;
esac
