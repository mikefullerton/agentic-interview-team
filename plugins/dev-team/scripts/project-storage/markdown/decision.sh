#!/bin/bash
# decision.sh — Decision CRUD for markdown project-storage
set -euo pipefail
source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: decision.sh <create|get|list|update|delete> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "title" "$PARSED_TITLE"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "rationale" "$PARSED_RATIONALE"
    require_flag "made-by" "$PARSED_MADE_BY"

    DIR="$(require_project "$PARSED_PROJECT")"
    DECISION_DIR="${DIR}/decisions"
    mkdir -p "$DECISION_DIR"

    ID="$(next_id "decision" "$DECISION_DIR")"
    SLUG="$(slugify "$PARSED_TITLE")"
    FILE="${DECISION_DIR}/${ID}-${SLUG}.md"

    DECISION_DATE="${PARSED_DATE:-$(today_iso)}"

    JSON=$(jq -n \
      --arg id "$ID" \
      --arg title "$PARSED_TITLE" \
      --arg rationale "$PARSED_RATIONALE" \
      --arg alternatives "$PARSED_ALTERNATIVES" \
      --arg made_by "$PARSED_MADE_BY" \
      --arg date "$DECISION_DATE" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        id: $id,
        title: $title,
        rationale: $rationale,
        alternatives: (if $alternatives == "" then null else $alternatives end),
        made_by: $made_by,
        date: $date,
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
    DECISION_DIR="${DIR}/decisions"

    FILE="$(find "$DECISION_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Decision not found: ${PARSED_ID}" >&2
      exit 1
    fi

    JSON="$(read_frontmatter "$FILE")"
    BODY="$(read_body "$FILE")"
    echo "$JSON" | jq --arg desc "$BODY" '. + {description: $desc}'
    ;;

  list)
    require_flag "project" "$PARSED_PROJECT"

    DIR="$(require_project "$PARSED_PROJECT")"
    DECISION_DIR="${DIR}/decisions"
    mkdir -p "$DECISION_DIR"

    RESULT="[]"
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      JSON="$(read_frontmatter "$file")"
      RESULT="$(echo "$RESULT" | jq --argjson item "$JSON" '. + [$item]')"
    done < <(find "$DECISION_DIR" -maxdepth 1 -name '*.md' 2>/dev/null | sort)

    echo "$RESULT"
    ;;

  update)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    DECISION_DIR="${DIR}/decisions"

    FILE="$(find "$DECISION_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Decision not found: ${PARSED_ID}" >&2
      exit 1
    fi

    UPDATES="{}"
    [[ -n "$PARSED_TITLE" ]]        && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_TITLE"        '. + {title: $v}')"
    [[ -n "$PARSED_RATIONALE" ]]    && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_RATIONALE"    '. + {rationale: $v}')"
    [[ -n "$PARSED_ALTERNATIVES" ]] && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_ALTERNATIVES" '. + {alternatives: $v}')"
    [[ -n "$PARSED_MADE_BY" ]]      && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_MADE_BY"      '. + {made_by: $v}')"
    [[ -n "$PARSED_DATE" ]]         && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_DATE"         '. + {date: $v}')"

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
    DECISION_DIR="${DIR}/decisions"

    FILE="$(find "$DECISION_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Decision not found: ${PARSED_ID}" >&2
      exit 1
    fi

    rm "$FILE"
    json_build id="$PARSED_ID" deleted="true"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: decision.sh <create|get|list|update|delete> [flags]" >&2
    exit 1
    ;;
esac
