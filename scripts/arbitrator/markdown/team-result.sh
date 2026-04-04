#!/bin/bash
# team-result.sh — Team-result resource for markdown arbitrator
# Actions: create, get, list, update
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: team-result.sh <create|get|list|update> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "result" "$PARSED_RESULT"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAMS_DIR="${DIR}/results/${PARSED_SPECIALIST}/teams"
    mkdir -p "$TEAMS_DIR"

    TEAM_RESULT_ID="${PARSED_SESSION}:team-result:${PARSED_SPECIALIST}:${PARSED_TEAM}"
    TEAM_FILE="${TEAMS_DIR}/${PARSED_TEAM}.json"

    jq -n \
      --arg team_result_id "$TEAM_RESULT_ID" \
      --arg session_id "$PARSED_SESSION" \
      --arg result_id "$PARSED_RESULT" \
      --arg specialist "$PARSED_SPECIALIST" \
      --arg team_name "$PARSED_TEAM" \
      --arg status "running" \
      --argjson iteration 0 \
      --arg verifier_feedback "" \
      --arg creation_date "$(now_iso)" \
      --arg modification_date "$(now_iso)" \
      '{
        team_result_id: $team_result_id,
        session_id: $session_id,
        result_id: $result_id,
        specialist: $specialist,
        team_name: $team_name,
        status: $status,
        iteration: $iteration,
        verifier_feedback: $verifier_feedback,
        creation_date: $creation_date,
        modification_date: $modification_date
      }' > "$TEAM_FILE"

    json_build team_result_id="$TEAM_RESULT_ID"
    ;;

  get)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAM_FILE="${DIR}/results/${PARSED_SPECIALIST}/teams/${PARSED_TEAM}.json"

    if [[ ! -f "$TEAM_FILE" ]]; then
      echo "Team-result not found: ${PARSED_SPECIALIST}/${PARSED_TEAM}" >&2
      exit 1
    fi

    cat "$TEAM_FILE"
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
    for team_file in "${RESULTS_BASE}"/*/teams/*.json; do
      [[ -f "$team_file" ]] || continue

      if [[ -n "$PARSED_SPECIALIST" ]]; then
        FILE_SPECIALIST=$(jq -r '.specialist' "$team_file")
        [[ "$FILE_SPECIALIST" == "$PARSED_SPECIALIST" ]] || continue
      fi

      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS=$(jq -r '.status' "$team_file")
        [[ "$FILE_STATUS" == "$PARSED_STATUS" ]] || continue
      fi

      OUTPUT=$(echo "$OUTPUT" | jq --argjson obj "$(cat "$team_file")" '. + [$obj]')
    done

    echo "$OUTPUT"
    ;;

  update)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAM_FILE="${DIR}/results/${PARSED_SPECIALIST}/teams/${PARSED_TEAM}.json"

    if [[ ! -f "$TEAM_FILE" ]]; then
      echo "Team-result not found: ${PARSED_SPECIALIST}/${PARSED_TEAM}" >&2
      exit 1
    fi

    UPDATED=$(cat "$TEAM_FILE")

    if [[ -n "$PARSED_STATUS" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --arg v "$PARSED_STATUS" '.status = $v')
    fi

    if [[ -n "$PARSED_ITERATION" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --argjson v "$PARSED_ITERATION" '.iteration = $v')
    fi

    if [[ -n "$PARSED_VERIFIER_FEEDBACK" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --arg v "$PARSED_VERIFIER_FEEDBACK" '.verifier_feedback = $v')
    fi

    UPDATED=$(echo "$UPDATED" | jq --arg v "$(now_iso)" '.modification_date = $v')

    echo "$UPDATED" > "$TEAM_FILE"

    json_build team_result_id="$(echo "$UPDATED" | jq -r '.team_result_id')"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: team-result.sh <create|get|list|update> [flags]" >&2
    exit 1
    ;;
esac
