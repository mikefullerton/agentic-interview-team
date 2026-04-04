#!/bin/bash
# milestone.sh — Milestone CRUD for markdown project-storage
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: milestone.sh <create|get|list|update|delete> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "name" "$PARSED_NAME"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "status" "$PARSED_STATUS"

    DIR="$(require_project "$PARSED_PROJECT")"
    MILESTONE_DIR="${DIR}/schedule"
    mkdir -p "$MILESTONE_DIR"

    ID="$(next_id "milestone" "$MILESTONE_DIR")"
    SLUG="$(slugify "$PARSED_NAME")"
    FILE="${MILESTONE_DIR}/${ID}-${SLUG}.md"

    JSON=$(jq -n \
      --arg id "$ID" \
      --arg name "$PARSED_NAME" \
      --arg status "$PARSED_STATUS" \
      --arg target_date "$PARSED_TARGET_DATE" \
      --arg dependencies "$PARSED_DEPENDENCIES" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        id: $id,
        name: $name,
        status: $status,
        target_date: (if $target_date == "" then null else $target_date end),
        dependencies: (if $dependencies == "" then null else $dependencies end),
        created: $created,
        modified: $modified
      }')

    write_item "$FILE" "$PARSED_DESCRIPTION" "$JSON"
    json_build id="$ID"
    ;;

  get)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    MILESTONE_DIR="${DIR}/schedule"

    FILE="$(find "$MILESTONE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Milestone not found: ${PARSED_ID}" >&2
      exit 1
    fi

    JSON="$(read_frontmatter "$FILE")"
    BODY="$(read_body "$FILE")"
    echo "$JSON" | jq --arg desc "$BODY" '. + {description: $desc}'
    ;;

  list)
    require_flag "project" "$PARSED_PROJECT"

    DIR="$(require_project "$PARSED_PROJECT")"
    MILESTONE_DIR="${DIR}/schedule"
    mkdir -p "$MILESTONE_DIR"

    RESULT="[]"
    while IFS= read -r -d '' file; do
      JSON="$(read_frontmatter "$file")"

      # Filter by --status if provided
      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS="$(echo "$JSON" | jq -r '.status // ""')"
        [[ "$FILE_STATUS" == "$PARSED_STATUS" ]] || continue
      fi

      RESULT="$(echo "$RESULT" | jq --argjson item "$JSON" '. + [$item]')"
    done < <(find "$MILESTONE_DIR" -maxdepth 1 -name '*.md' -print0 2>/dev/null)

    echo "$RESULT"
    ;;

  update)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    MILESTONE_DIR="${DIR}/schedule"

    FILE="$(find "$MILESTONE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Milestone not found: ${PARSED_ID}" >&2
      exit 1
    fi

    UPDATES="{}"
    [[ -n "$PARSED_NAME" ]]         && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_NAME"         '. + {name: $v}')"
    [[ -n "$PARSED_STATUS" ]]       && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_STATUS"       '. + {status: $v}')"
    [[ -n "$PARSED_TARGET_DATE" ]]  && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_TARGET_DATE"  '. + {target_date: $v}')"
    [[ -n "$PARSED_DEPENDENCIES" ]] && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_DEPENDENCIES" '. + {dependencies: $v}')"

    update_item "$FILE" "$UPDATES"
    json_build id="$PARSED_ID"
    ;;

  delete)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    MILESTONE_DIR="${DIR}/schedule"

    FILE="$(find "$MILESTONE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Milestone not found: ${PARSED_ID}" >&2
      exit 1
    fi

    rm "$FILE"
    json_build id="$PARSED_ID" deleted="true"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: milestone.sh <create|get|list|update|delete> [flags]" >&2
    exit 1
    ;;
esac
