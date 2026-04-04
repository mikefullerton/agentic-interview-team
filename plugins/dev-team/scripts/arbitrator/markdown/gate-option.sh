#!/bin/bash
# gate-option.sh — Gate options for markdown arbitrator
# Actions: add
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: gate-option.sh <add> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  add)
    require_flag "message" "$PARSED_MESSAGE"
    require_flag "option-text" "$PARSED_OPTION_TEXT"
    require_flag "is-default" "$PARSED_IS_DEFAULT"
    require_flag "sort-order" "$PARSED_SORT_ORDER"

    # Composite ID format: <session_id>:message:<seq>
    SESSION_ID="${PARSED_MESSAGE%%:message:*}"
    MSG_SEQ="${PARSED_MESSAGE##*:message:}"

    DIR="$(require_session "$SESSION_ID")"
    GATE_DIR="${DIR}/gate-options"
    mkdir -p "$GATE_DIR"

    FILE="${GATE_DIR}/${MSG_SEQ}-option-${PARSED_SORT_ORDER}.json"

    ID="${PARSED_MESSAGE}:option:${PARSED_SORT_ORDER}"

    json_build \
      id="$ID" \
      message_id="$PARSED_MESSAGE" \
      option_text="$PARSED_OPTION_TEXT" \
      is_default="$PARSED_IS_DEFAULT" \
      sort_order="$PARSED_SORT_ORDER" \
      > "$FILE"

    cat "$FILE"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: gate-option.sh <add> [flags]" >&2
    exit 1
    ;;
esac
