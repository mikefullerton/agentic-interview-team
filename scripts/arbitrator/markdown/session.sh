#!/bin/bash
# session.sh — Session lifecycle for markdown arbitrator
# Actions: create, get, list, add-path
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: session.sh <create|get|list|add-path> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "playbook" "$PARSED_PLAYBOOK"
    require_flag "team-lead" "$PARSED_TEAM_LEAD"
    require_flag "user" "$PARSED_USER"
    require_flag "machine" "$PARSED_MACHINE"

    SESSION_ID=$(new_session_id)
    DIR="$(session_dir "$SESSION_ID")"
    mkdir -p "$DIR"

    json_build \
      session_id="$SESSION_ID" \
      playbook="$PARSED_PLAYBOOK" \
      team_lead="$PARSED_TEAM_LEAD" \
      user="$PARSED_USER" \
      machine="$PARSED_MACHINE" \
      creation_date="$(now_iso)" \
      > "$DIR/session.json"

    json_build session_id="$SESSION_ID"
    ;;

  get)
    require_flag "session" "$PARSED_SESSION"
    DIR="$(require_session "$PARSED_SESSION")"
    cat "$DIR/session.json"
    ;;

  list)
    if [[ ! -d "$SESSION_BASE" ]]; then
      echo "[]"
      exit 0
    fi

    RESULTS="[]"
    for session_file in "$SESSION_BASE"/*/session.json; do
      [[ -f "$session_file" ]] || continue
      MATCH=true

      if [[ -n "$PARSED_PLAYBOOK" ]]; then
        FILE_PLAYBOOK=$(jq -r '.playbook' "$session_file")
        [[ "$FILE_PLAYBOOK" == "$PARSED_PLAYBOOK" ]] || MATCH=false
      fi

      if [[ -n "$PARSED_STATUS" ]]; then
        SESSION_ID=$(jq -r '.session_id' "$session_file")
        SESSION_DIR="$(session_dir "$SESSION_ID")"
        STATE_DIR="${SESSION_DIR}/state"
        if [[ -d "$STATE_DIR" ]]; then
          LATEST_STATE=$(find "$STATE_DIR" -name '*.json' | sort | tail -1)
          if [[ -n "$LATEST_STATE" ]]; then
            CURRENT_STATE=$(jq -r '.state' "$LATEST_STATE")
            [[ "$CURRENT_STATE" == "$PARSED_STATUS" ]] || MATCH=false
          else
            MATCH=false
          fi
        else
          MATCH=false
        fi
      fi

      if $MATCH; then
        RESULTS=$(echo "$RESULTS" | jq --argjson obj "$(cat "$session_file")" '. + [$obj]')
      fi
    done

    echo "$RESULTS"
    ;;

  add-path)
    require_flag "session" "$PARSED_SESSION"
    require_flag "path" "$PARSED_PATH"
    require_flag "type" "$PARSED_TYPE"

    DIR="$(require_session "$PARSED_SESSION")"
    PATHS_FILE="$DIR/paths.jsonl"

    json_build \
      session_id="$PARSED_SESSION" \
      path="$PARSED_PATH" \
      type="$PARSED_TYPE" \
      creation_date="$(now_iso)" \
      >> "$PATHS_FILE"

    json_build session_id="$PARSED_SESSION" path="$PARSED_PATH" type="$PARSED_TYPE"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: session.sh <create|get|list|add-path> [flags]" >&2
    exit 1
    ;;
esac
