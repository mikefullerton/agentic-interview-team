#!/bin/bash
# interpretation.sh — Interpretation resource for markdown arbitrator
# Actions: create, list
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: interpretation.sh <create|list> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "finding" "$PARSED_FINDING"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "interpretation" "$PARSED_INTERPRETATION"

    DIR="$(require_session "$PARSED_SESSION")"

    # Parse composite finding ID: <session-id>:finding:<specialist>:<seq>
    FINDING_REMAINDER="${PARSED_FINDING#*:finding:}"
    FINDING_SEQ="${FINDING_REMAINDER##*:}"

    if [[ -z "$FINDING_SEQ" || "$FINDING_REMAINDER" == "$PARSED_FINDING" ]]; then
      echo "Invalid finding ID format: ${PARSED_FINDING}" >&2
      exit 1
    fi

    INTERP_DIR="${DIR}/results/${PARSED_SPECIALIST}/interpretations"
    mkdir -p "$INTERP_DIR"

    INTERP_FILE="${INTERP_DIR}/${FINDING_SEQ}-interpretation.json"
    INTERPRETATION_ID="${PARSED_SESSION}:interpretation:${PARSED_SPECIALIST}:${FINDING_SEQ}"

    json_build \
      interpretation_id="$INTERPRETATION_ID" \
      finding_id="$PARSED_FINDING" \
      session_id="$PARSED_SESSION" \
      specialist="$PARSED_SPECIALIST" \
      interpretation="$PARSED_INTERPRETATION" \
      creation_date="$(now_iso)" \
      > "$INTERP_FILE"

    json_build interpretation_id="$INTERPRETATION_ID"
    ;;

  list)
    require_flag "finding" "$PARSED_FINDING"

    # Parse composite finding ID: <session-id>:finding:<specialist>:<seq>
    SESSION_ID="${PARSED_FINDING%%:finding:*}"
    FINDING_REMAINDER="${PARSED_FINDING#*:finding:}"
    SPECIALIST="${FINDING_REMAINDER%%:*}"
    FINDING_SEQ="${FINDING_REMAINDER##*:}"

    if [[ -z "$SESSION_ID" || -z "$SPECIALIST" || -z "$FINDING_SEQ" || "$SESSION_ID" == "$PARSED_FINDING" ]]; then
      echo "Invalid finding ID format: ${PARSED_FINDING}" >&2
      exit 1
    fi

    DIR="$(session_dir "$SESSION_ID")"
    INTERP_DIR="${DIR}/results/${SPECIALIST}/interpretations"

    if [[ ! -d "$INTERP_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    OUTPUT="[]"
    for interp_file in "${INTERP_DIR}/${FINDING_SEQ}-interpretation.json"; do
      [[ -f "$interp_file" ]] || continue
      OUTPUT=$(echo "$OUTPUT" | jq --argjson obj "$(cat "$interp_file")" '. + [$obj]')
    done

    echo "$OUTPUT"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: interpretation.sh <create|list> [flags]" >&2
    exit 1
    ;;
esac
