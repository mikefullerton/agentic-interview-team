#!/bin/bash
# dependency.sh — Dependency CRUD for markdown project-storage
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: dependency.sh <create|get|list|update|delete> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "name" "$PARSED_NAME"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "type" "$PARSED_TYPE"
    require_flag "status" "$PARSED_STATUS"

    DIR="$(require_project "$PARSED_PROJECT")"
    DEP_DIR="${DIR}/dependencies"
    mkdir -p "$DEP_DIR"

    ID="$(next_id "dependency" "$DEP_DIR")"
    SLUG="$(slugify "$PARSED_NAME")"
    FILE="${DEP_DIR}/${ID}-${SLUG}.md"

    JSON=$(jq -n \
      --arg id "$ID" \
      --arg name "$PARSED_NAME" \
      --arg status "$PARSED_STATUS" \
      --arg type "$PARSED_TYPE" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        id: $id,
        name: $name,
        status: $status,
        type: $type,
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
    DEP_DIR="${DIR}/dependencies"

    FILE="$(find "$DEP_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Dependency not found: ${PARSED_ID}" >&2
      exit 1
    fi

    JSON="$(read_frontmatter "$FILE")"
    BODY="$(read_body "$FILE")"
    echo "$JSON" | jq --arg desc "$BODY" '. + {description: $desc}'
    ;;

  list)
    require_flag "project" "$PARSED_PROJECT"

    DIR="$(require_project "$PARSED_PROJECT")"
    DEP_DIR="${DIR}/dependencies"
    mkdir -p "$DEP_DIR"

    RESULT="[]"
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      JSON="$(read_frontmatter "$file")"

      # Filter by --status if provided
      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS="$(echo "$JSON" | jq -r '.status // ""')"
        [[ "$FILE_STATUS" != "$PARSED_STATUS" ]] && continue
      fi

      # Filter by --type if provided
      if [[ -n "$PARSED_TYPE" ]]; then
        FILE_TYPE="$(echo "$JSON" | jq -r '.type // ""')"
        [[ "$FILE_TYPE" != "$PARSED_TYPE" ]] && continue
      fi

      RESULT="$(echo "$RESULT" | jq --argjson item "$JSON" '. + [$item]')"
    done < <(find "$DEP_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | sort)

    echo "$RESULT"
    ;;

  update)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    DEP_DIR="${DIR}/dependencies"

    FILE="$(find "$DEP_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Dependency not found: ${PARSED_ID}" >&2
      exit 1
    fi

    UPDATES="{}"
    [[ -n "$PARSED_NAME" ]]   && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_NAME"   '. + {name: $v}')"
    [[ -n "$PARSED_STATUS" ]] && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_STATUS" '. + {status: $v}')"
    [[ -n "$PARSED_TYPE" ]]   && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_TYPE"   '. + {type: $v}')"

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
    DEP_DIR="${DIR}/dependencies"

    FILE="$(find "$DEP_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Dependency not found: ${PARSED_ID}" >&2
      exit 1
    fi

    rm "$FILE"
    json_build id="$PARSED_ID" deleted="true"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: dependency.sh <create|get|list|update|delete> [flags]" >&2
    exit 1
    ;;
esac
