#!/bin/bash
# issue.sh — Issue CRUD for markdown project-storage
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: issue.sh <create|get|list|update|delete> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "title" "$PARSED_TITLE"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "severity" "$PARSED_SEVERITY"
    require_flag "status" "$PARSED_STATUS"

    DIR="$(require_project "$PARSED_PROJECT")"
    ISSUE_DIR="${DIR}/issues"
    mkdir -p "$ISSUE_DIR"

    ID="$(next_id "issue" "$ISSUE_DIR")"
    SLUG="$(slugify "$PARSED_TITLE")"
    FILE="${ISSUE_DIR}/${ID}-${SLUG}.md"

    JSON=$(jq -n \
      --arg id "$ID" \
      --arg title "$PARSED_TITLE" \
      --arg status "$PARSED_STATUS" \
      --arg severity "$PARSED_SEVERITY" \
      --arg source "$PARSED_SOURCE" \
      --arg related_findings "$PARSED_RELATED_FINDINGS" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        id: $id,
        title: $title,
        status: $status,
        severity: $severity,
        source: (if $source == "" then null else $source end),
        related_findings: (if $related_findings == "" then null else $related_findings end),
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
    ISSUE_DIR="${DIR}/issues"

    FILE="$(find "$ISSUE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Issue not found: ${PARSED_ID}" >&2
      exit 1
    fi

    JSON="$(read_frontmatter "$FILE")"
    BODY="$(read_body "$FILE")"
    echo "$JSON" | jq --arg desc "$BODY" '. + {description: $desc}'
    ;;

  list)
    require_flag "project" "$PARSED_PROJECT"

    DIR="$(require_project "$PARSED_PROJECT")"
    ISSUE_DIR="${DIR}/issues"
    mkdir -p "$ISSUE_DIR"

    RESULT="[]"
    while IFS= read -r -d '' file; do
      JSON="$(read_frontmatter "$file")"

      # Filter by --status if provided
      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS="$(echo "$JSON" | jq -r '.status // ""')"
        [[ "$FILE_STATUS" == "$PARSED_STATUS" ]] || continue
      fi

      # Filter by --severity if provided
      if [[ -n "$PARSED_SEVERITY" ]]; then
        FILE_SEVERITY="$(echo "$JSON" | jq -r '.severity // ""')"
        [[ "$FILE_SEVERITY" == "$PARSED_SEVERITY" ]] || continue
      fi

      RESULT="$(echo "$RESULT" | jq --argjson item "$JSON" '. + [$item]')"
    done < <(find "$ISSUE_DIR" -maxdepth 1 -name '*.md' -print0 2>/dev/null)

    echo "$RESULT"
    ;;

  update)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    ISSUE_DIR="${DIR}/issues"

    FILE="$(find "$ISSUE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Issue not found: ${PARSED_ID}" >&2
      exit 1
    fi

    UPDATES="{}"
    [[ -n "$PARSED_TITLE" ]]            && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_TITLE"            '. + {title: $v}')"
    [[ -n "$PARSED_STATUS" ]]           && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_STATUS"           '. + {status: $v}')"
    [[ -n "$PARSED_SEVERITY" ]]         && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_SEVERITY"         '. + {severity: $v}')"
    [[ -n "$PARSED_SOURCE" ]]           && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_SOURCE"           '. + {source: $v}')"
    [[ -n "$PARSED_RELATED_FINDINGS" ]] && UPDATES="$(echo "$UPDATES" | jq --arg v "$PARSED_RELATED_FINDINGS" '. + {related_findings: $v}')"

    update_item "$FILE" "$UPDATES"
    json_build id="$PARSED_ID"
    ;;

  delete)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "id" "$PARSED_ID"

    DIR="$(require_project "$PARSED_PROJECT")"
    ISSUE_DIR="${DIR}/issues"

    FILE="$(find "$ISSUE_DIR" -maxdepth 1 -name "${PARSED_ID}-*.md" 2>/dev/null | head -1)"
    if [[ -z "$FILE" ]]; then
      echo "Issue not found: ${PARSED_ID}" >&2
      exit 1
    fi

    rm "$FILE"
    json_build id="$PARSED_ID" deleted="true"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: issue.sh <create|get|list|update|delete> [flags]" >&2
    exit 1
    ;;
esac
