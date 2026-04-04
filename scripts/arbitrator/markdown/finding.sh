#!/bin/bash
# finding.sh — Finding resource for markdown arbitrator
# Actions: create, list, get, link-artifact
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: finding.sh <create|list|get|link-artifact> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "result" "$PARSED_RESULT"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "category" "$PARSED_CATEGORY"
    require_flag "severity" "$PARSED_SEVERITY"
    require_flag "title" "$PARSED_TITLE"
    require_flag "detail" "$PARSED_DETAIL"

    DIR="$(require_session "$PARSED_SESSION")"
    FINDINGS_DIR="${DIR}/results/${PARSED_SPECIALIST}/findings"
    mkdir -p "$FINDINGS_DIR"

    SEQ=$(next_seq "$FINDINGS_DIR")
    SLUG=$(slugify "$PARSED_TITLE")
    FINDING_FILE="${FINDINGS_DIR}/${SEQ}-${SLUG}.json"
    FINDING_ID="${PARSED_SESSION}:finding:${PARSED_SPECIALIST}:${SEQ}"

    jq -n \
      --arg finding_id "$FINDING_ID" \
      --arg result_id "$PARSED_RESULT" \
      --arg session_id "$PARSED_SESSION" \
      --arg specialist "$PARSED_SPECIALIST" \
      --arg category "$PARSED_CATEGORY" \
      --arg severity "$PARSED_SEVERITY" \
      --arg title "$PARSED_TITLE" \
      --arg detail "$PARSED_DETAIL" \
      --arg creation_date "$(now_iso)" \
      '{
        finding_id: $finding_id,
        result_id: $result_id,
        session_id: $session_id,
        specialist: $specialist,
        category: $category,
        severity: $severity,
        title: $title,
        detail: $detail,
        creation_date: $creation_date,
        linked_artifacts: []
      }' > "$FINDING_FILE"

    json_build finding_id="$FINDING_ID"
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
    for finding_file in "${RESULTS_BASE}"/*/findings/*.json; do
      [[ -f "$finding_file" ]] || continue

      if [[ -n "$PARSED_SPECIALIST" ]]; then
        FILE_SPECIALIST=$(jq -r '.specialist' "$finding_file")
        [[ "$FILE_SPECIALIST" == "$PARSED_SPECIALIST" ]] || continue
      fi

      if [[ -n "$PARSED_SEVERITY" ]]; then
        FILE_SEVERITY=$(jq -r '.severity' "$finding_file")
        [[ "$FILE_SEVERITY" == "$PARSED_SEVERITY" ]] || continue
      fi

      OUTPUT=$(echo "$OUTPUT" | jq --argjson obj "$(cat "$finding_file")" '. + [$obj]')
    done

    echo "$OUTPUT"
    ;;

  get)
    require_flag "finding" "$PARSED_FINDING"

    # Parse composite ID: <session-id>:finding:<specialist>:<seq>
    # Extract session_id (everything before :finding:)
    SESSION_ID="${PARSED_FINDING%%:finding:*}"
    REMAINDER="${PARSED_FINDING#*:finding:}"
    SPECIALIST="${REMAINDER%%:*}"
    SEQ="${REMAINDER##*:}"

    if [[ -z "$SESSION_ID" || -z "$SPECIALIST" || -z "$SEQ" || "$SESSION_ID" == "$PARSED_FINDING" ]]; then
      echo "Invalid finding ID format: ${PARSED_FINDING}" >&2
      exit 1
    fi

    DIR="$(require_session "$SESSION_ID")"
    FINDINGS_DIR="${DIR}/results/${SPECIALIST}/findings"

    FINDING_FILE=$(find "$FINDINGS_DIR" -maxdepth 1 -name "${SEQ}-*.json" 2>/dev/null | head -1)
    if [[ -z "$FINDING_FILE" || ! -f "$FINDING_FILE" ]]; then
      echo "Finding not found: ${PARSED_FINDING}" >&2
      exit 1
    fi

    cat "$FINDING_FILE"
    ;;

  link-artifact)
    require_flag "finding" "$PARSED_FINDING"
    require_flag "artifact" "$PARSED_ARTIFACT"

    # Parse composite ID: <session-id>:finding:<specialist>:<seq>
    SESSION_ID="${PARSED_FINDING%%:finding:*}"
    REMAINDER="${PARSED_FINDING#*:finding:}"
    SPECIALIST="${REMAINDER%%:*}"
    SEQ="${REMAINDER##*:}"

    if [[ -z "$SESSION_ID" || -z "$SPECIALIST" || -z "$SEQ" || "$SESSION_ID" == "$PARSED_FINDING" ]]; then
      echo "Invalid finding ID format: ${PARSED_FINDING}" >&2
      exit 1
    fi

    DIR="$(require_session "$SESSION_ID")"
    FINDINGS_DIR="${DIR}/results/${SPECIALIST}/findings"

    FINDING_FILE=$(find "$FINDINGS_DIR" -maxdepth 1 -name "${SEQ}-*.json" 2>/dev/null | head -1)
    if [[ -z "$FINDING_FILE" || ! -f "$FINDING_FILE" ]]; then
      echo "Finding not found: ${PARSED_FINDING}" >&2
      exit 1
    fi

    UPDATED=$(jq --arg artifact "$PARSED_ARTIFACT" '.linked_artifacts += [$artifact]' "$FINDING_FILE")
    echo "$UPDATED" > "$FINDING_FILE"

    json_build finding_id="$PARSED_FINDING" artifact_id="$PARSED_ARTIFACT"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: finding.sh <create|list|get|link-artifact> [flags]" >&2
    exit 1
    ;;
esac
