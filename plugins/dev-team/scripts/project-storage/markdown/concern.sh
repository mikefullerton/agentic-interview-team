#!/bin/bash
# concern.sh — Concern CRUD for markdown project-storage
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: concern.sh <create|get|list|update|delete> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "title" "$PARSED_TITLE"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "raised-by" "$PARSED_RAISED_BY"
    require_flag "status" "$PARSED_STATUS"

    DIR="$(require_project "$PARSED_PROJECT")"
    CONCERN_DIR="${DIR}/concerns"
    mkdir -p "$CONCERN_DIR"

    ID="$(next_id "concern" "$CONCERN_DIR")"
    SLUG="$(slugify "$PARSED_TITLE")"
    FILE="${CONCERN_DIR}/${ID}-${SLUG}.md"

    JSON=$(jq -n \
      --arg id "$ID" \
      --arg title "$PARSED_TITLE" \
      --arg status "$PARSED_STATUS" \
      --arg raised_by "$PARSED_RAISED_BY" \
      --arg related_to "$PARSED_RELATED_TO" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        id: $id,
        title: $title,
        status: $status,
        raised_by: $raised_by,
        related_to: (if $related_to == "" then null else $related_to end),
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
    CONCERN_DIR="${DIR}/concerns"

    FILE="$(find "$CONCERN_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Concern not found: ${PARSED_ID}" >&2
      exit 1
    fi

    JSON="$(read_frontmatter "$FILE")"
    BODY="$(read_body "$FILE")"
    echo "$JSON" | jq --arg desc "$BODY" '. + {description: $desc}'
    ;;

  list)
    require_flag "project" "$PARSED_PROJECT"

    DIR="$(require_project "$PARSED_PROJECT")"
    CONCERN_DIR="${DIR}/concerns"
    mkdir -p "$CONCERN_DIR"

    RESULT="[]"
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      JSON="$(read_frontmatter "$file")"

      # Filter by --status if provided
      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS="$(echo "$JSON" | jq -r '.status // ""')"
        [[ "$FILE_STATUS" != "$PARSED_STATUS" ]] && continue
      fi

      RESULT="$(echo "$RESULT" | jq --argjson item "$JSON" '. + [$item]')"
    done < <(find "$CONCERN_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | sort)

    echo "$RESULT"
    ;;

  update)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    CONCERN_DIR="${DIR}/concerns"

    FILE="$(find "$CONCERN_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Concern not found: ${PARSED_ID}" >&2
      exit 1
    fi

    UPDATES="{}"
    [[ -n "$PARSED_TITLE" ]]      && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_TITLE"      '. + {title: $v}')"
    [[ -n "$PARSED_STATUS" ]]     && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_STATUS"     '. + {status: $v}')"
    [[ -n "$PARSED_RAISED_BY" ]]  && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_RAISED_BY"  '. + {raised_by: $v}')"
    [[ -n "$PARSED_RELATED_TO" ]] && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_RELATED_TO" '. + {related_to: $v}')"

    if [[ -n "$PARSED_DESCRIPTION" ]]; then
      CURRENT_JSON="$(read_frontmatter "$FILE")"
      MERGED="$(echo "$CURRENT_JSON" | jq --argjson updates "$UPDATES" --arg mod "$(today_iso)" '. + $updates + {modified: $mod}')"
      write_item "$FILE" "$PARSED_DESCRIPTION" "$MERGED"
    else
      update_item "$FILE" "$UPDATES"
    fi

    json_build id="$PARSED_ID"
    ;;

  delete)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    CONCERN_DIR="${DIR}/concerns"

    FILE="$(find "$CONCERN_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Concern not found: ${PARSED_ID}" >&2
      exit 1
    fi

    rm "$FILE"
    json_build id="$PARSED_ID" deleted="true"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: concern.sh <create|get|list|update|delete> [flags]" >&2
    exit 1
    ;;
esac
