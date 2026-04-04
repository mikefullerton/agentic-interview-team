#!/bin/bash
# report.sh — Progressive disclosure queries for markdown arbitrator
# Actions: overview, specialist, finding, trace
# Reports are NOT stored — they compose from existing data.
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: report.sh <overview|specialist|finding|trace> [flags]}"; shift
parse_flags "$@"

ARBITRATOR="$(cd "$(dirname "$0")/../.." && pwd)/arbitrator.sh"

case "$ACTION" in
  overview)
    require_flag "session" "$PARSED_SESSION"
    DIR="$(require_session "$PARSED_SESSION")"

    # Session metadata
    SESSION=$(cat "$DIR/session.json")

    # Current state (latest state transition)
    CURRENT_STATE="null"
    STATE_DIR="$DIR/state"
    if [[ -d "$STATE_DIR" ]]; then
      LATEST=$(find "$STATE_DIR" -name '*.json' | sort | tail -1)
      if [[ -n "$LATEST" ]]; then
        CURRENT_STATE=$(cat "$LATEST")
      fi
    fi

    # Specialist summary
    SPECIALISTS="[]"
    RESULTS_DIR="$DIR/results"
    if [[ -d "$RESULTS_DIR" ]]; then
      for spec_dir in "$RESULTS_DIR"/*/; do
        [[ -d "$spec_dir" ]] || continue
        SPEC=$(basename "$spec_dir")
        FINDINGS_COUNT=0
        FINDINGS_DIR="$spec_dir/findings"
        if [[ -d "$FINDINGS_DIR" ]]; then
          FINDINGS_COUNT=$(find "$FINDINGS_DIR" -name '*.json' | wc -l | tr -d ' ')
        fi
        SPECIALISTS=$(echo "$SPECIALISTS" | jq \
          --arg specialist "$SPEC" \
          --argjson findings_count "$FINDINGS_COUNT" \
          '. + [{"specialist": $specialist, "findings_count": $findings_count}]')
      done
    fi

    jq -n \
      --argjson session "$SESSION" \
      --argjson current_state "$CURRENT_STATE" \
      --argjson specialists "$SPECIALISTS" \
      '{session: $session, current_state: $current_state, specialists: $specialists}'
    ;;

  specialist)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"
    DIR="$(require_session "$PARSED_SESSION")"

    SPEC_DIR="$DIR/results/$PARSED_SPECIALIST"
    if [[ ! -d "$SPEC_DIR" ]]; then
      echo "{\"error\": \"No results for specialist: ${PARSED_SPECIALIST}\"}" >&2
      exit 1
    fi

    # Result metadata
    RESULT=$(cat "$SPEC_DIR/result.json")

    # All findings
    FINDINGS="[]"
    FINDINGS_DIR="$SPEC_DIR/findings"
    if [[ -d "$FINDINGS_DIR" ]]; then
      for f in "$FINDINGS_DIR"/*.json; do
        [[ -f "$f" ]] || continue
        FINDINGS=$(echo "$FINDINGS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    # All interpretations
    INTERPRETATIONS="[]"
    INTERP_DIR="$SPEC_DIR/interpretations"
    if [[ -d "$INTERP_DIR" ]]; then
      for f in "$INTERP_DIR"/*.json; do
        [[ -f "$f" ]] || continue
        INTERPRETATIONS=$(echo "$INTERPRETATIONS" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    # All references
    REFERENCES="[]"
    REF_DIR="$SPEC_DIR/references"
    if [[ -d "$REF_DIR" ]]; then
      for f in "$REF_DIR"/*.json; do
        [[ -f "$f" ]] || continue
        REFERENCES=$(echo "$REFERENCES" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    jq -n \
      --argjson result "$RESULT" \
      --argjson findings "$FINDINGS" \
      --argjson interpretations "$INTERPRETATIONS" \
      --argjson references "$REFERENCES" \
      '{result: $result, findings: $findings, interpretations: $interpretations, references: $references}'
    ;;

  finding)
    require_flag "finding" "$PARSED_FINDING"

    # Parse composite ID: <session-id>:finding:<specialist>:<seq>
    SESSION_ID="${PARSED_FINDING%%:finding:*}"
    REMAINDER="${PARSED_FINDING#*:finding:}"
    SPECIALIST="${REMAINDER%%:*}"
    SEQ="${REMAINDER##*:}"

    DIR="$(require_session "$SESSION_ID")"
    FINDINGS_DIR="$DIR/results/$SPECIALIST/findings"

    # Find the file matching the sequence
    FINDING_FILE=$(find "$FINDINGS_DIR" -name "${SEQ}-*.json" 2>/dev/null | head -1)
    if [[ -z "$FINDING_FILE" || ! -f "$FINDING_FILE" ]]; then
      echo "Finding not found: ${PARSED_FINDING}" >&2
      exit 1
    fi

    FINDING=$(cat "$FINDING_FILE")

    # Find matching interpretation
    INTERP_DIR="$DIR/results/$SPECIALIST/interpretations"
    INTERPRETATION="null"
    INTERP_FILE="$INTERP_DIR/${SEQ}-interpretation.json"
    if [[ -f "$INTERP_FILE" ]]; then
      INTERPRETATION=$(cat "$INTERP_FILE")
    fi

    # Linked artifacts
    LINKED_ARTIFACTS="[]"
    ARTIFACT_IDS=$(echo "$FINDING" | jq -r '.linked_artifacts[]? // empty')
    if [[ -n "$ARTIFACT_IDS" ]]; then
      ARTIFACTS_DIR="$DIR/artifacts"
      while IFS= read -r aid; do
        AID_SEQ="${aid##*:}"
        AF=$(find "$ARTIFACTS_DIR" -name "${AID_SEQ}-*.json" 2>/dev/null | head -1)
        if [[ -n "$AF" && -f "$AF" ]]; then
          LINKED_ARTIFACTS=$(echo "$LINKED_ARTIFACTS" | jq --argjson obj "$(cat "$AF")" '. + [$obj]')
        fi
      done <<< "$ARTIFACT_IDS"
    fi

    jq -n \
      --argjson finding "$FINDING" \
      --argjson interpretation "$INTERPRETATION" \
      --argjson linked_artifacts "$LINKED_ARTIFACTS" \
      '{finding: $finding, interpretation: $interpretation, linked_artifacts: $linked_artifacts}'
    ;;

  trace)
    require_flag "session" "$PARSED_SESSION"
    DIR="$(require_session "$PARSED_SESSION")"

    # All state transitions in order
    STATES="[]"
    STATE_DIR="$DIR/state"
    if [[ -d "$STATE_DIR" ]]; then
      for f in $(find "$STATE_DIR" -name '*.json' | sort); do
        STATES=$(echo "$STATES" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    # All retries in order
    RETRIES="[]"
    RETRY_DIR="$DIR/retries"
    if [[ -d "$RETRY_DIR" ]]; then
      for f in $(find "$RETRY_DIR" -name '*.json' | sort); do
        RETRIES=$(echo "$RETRIES" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    # All messages in order
    MESSAGES="[]"
    MSG_DIR="$DIR/messages"
    if [[ -d "$MSG_DIR" ]]; then
      for f in $(find "$MSG_DIR" -name '*.json' | sort); do
        MESSAGES=$(echo "$MESSAGES" | jq --argjson obj "$(cat "$f")" '. + [$obj]')
      done
    fi

    jq -n \
      --argjson states "$STATES" \
      --argjson retries "$RETRIES" \
      --argjson messages "$MESSAGES" \
      '{states: $states, retries: $retries, messages: $messages}'
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: report.sh <overview|specialist|finding|trace> [flags]" >&2
    exit 1
    ;;
esac
