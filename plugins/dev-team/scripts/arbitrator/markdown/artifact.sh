#!/bin/bash
# artifact.sh — Artifact tracking for markdown arbitrator
# Actions: create, list, link-state
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: artifact.sh <create|list|link-state> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "artifact" "$PARSED_ARTIFACT"

    DIR="$(require_session "$PARSED_SESSION")"
    ARTIFACT_DIR="${DIR}/artifacts"
    SEQ=$(next_seq "$ARTIFACT_DIR")
    SLUG=$(slugify "$PARSED_ARTIFACT")
    FILE="${ARTIFACT_DIR}/${SEQ}-${SLUG}.json"

    ARTIFACT_ID="${PARSED_SESSION}:artifact:${SEQ}"

    jq -n \
      --arg artifact_id "$ARTIFACT_ID" \
      --arg session_id "$PARSED_SESSION" \
      --arg artifact "$PARSED_ARTIFACT" \
      --arg message "$PARSED_MESSAGE" \
      --arg description "$PARSED_DESCRIPTION" \
      --arg creation_date "$(now_iso)" \
      '{
        artifact_id: $artifact_id,
        session_id: $session_id,
        artifact: $artifact,
        message: $message,
        description: $description,
        creation_date: $creation_date,
        linked_states: []
      }' > "$FILE"

    json_build artifact_id="$ARTIFACT_ID"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    ARTIFACT_DIR="${DIR}/artifacts"

    if [[ ! -d "$ARTIFACT_DIR" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for f in $(find "$ARTIFACT_DIR" -maxdepth 1 -name '*.json' 2>/dev/null | sort); do
      [[ -f "$f" ]] || continue
      RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
    done

    echo "$RESULTS"
    ;;

  link-state)
    require_flag "artifact" "$PARSED_ARTIFACT"
    require_flag "state" "$PARSED_STATE"

    # Parse session ID from composite artifact ID: <session-id>:artifact:NNNN
    SESSION_ID="${PARSED_ARTIFACT%%:artifact:*}"
    SEQ="${PARSED_ARTIFACT##*:artifact:}"

    DIR="$(require_session "$SESSION_ID")"
    ARTIFACT_DIR="${DIR}/artifacts"

    FILE=$(find "$ARTIFACT_DIR" -maxdepth 1 -name "${SEQ}-*.json" 2>/dev/null | head -1)
    if [[ -z "$FILE" ]]; then
      echo "Artifact not found: ${PARSED_ARTIFACT}" >&2
      exit 1
    fi

    UPDATED=$(jq --arg state_id "$PARSED_STATE" '.linked_states += [$state_id]' "$FILE")
    echo "$UPDATED" > "$FILE"
    echo "$UPDATED"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: artifact.sh <create|list|link-state> [flags]" >&2
    exit 1
    ;;
esac
