#!/bin/bash
# project.sh — Project lifecycle for markdown project-storage
# Actions: init, status, link-cookbook, unlink-cookbook
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: project.sh <init|status|link-cookbook|unlink-cookbook> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  init)
    require_flag "name" "$PARSED_NAME"
    require_flag "description" "$PARSED_DESCRIPTION"
    require_flag "path" "$PARSED_PATH"

    DIR="$(project_dir "$PARSED_PATH")"
    if [[ -d "$DIR" ]]; then
      echo "Project already exists at: ${PARSED_PATH}" >&2
      exit 1
    fi

    mkdir -p "$DIR"/{schedule,todos,issues,concerns,dependencies,decisions}

    jq -n \
      --arg name "$PARSED_NAME" \
      --arg description "$PARSED_DESCRIPTION" \
      --arg created "$(today_iso)" \
      --arg modified "$(today_iso)" \
      '{
        name: $name,
        description: $description,
        created: $created,
        modified: $modified,
        cookbook_projects: []
      }' > "$DIR/manifest.json"

    json_build name="$PARSED_NAME" path="$PARSED_PATH"
    ;;

  status)
    require_flag "project" "$PARSED_PROJECT"
    DIR="$(require_project "$PARSED_PROJECT")"

    MANIFEST=$(cat "$DIR/manifest.json")

    # Count items per type
    COUNTS="{}"
    for type_dir in schedule todos issues concerns dependencies decisions; do
      COUNT=$(find "$DIR/$type_dir" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
      COUNTS=$(echo "$COUNTS" | jq --arg type "$type_dir" --argjson count "$COUNT" '. + {($type): $count}')
    done

    echo "$MANIFEST" | jq --argjson counts "$COUNTS" '. + {item_counts: $counts}'
    ;;

  link-cookbook)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "path" "$PARSED_PATH"
    DIR="$(require_project "$PARSED_PROJECT")"

    MANIFEST="$DIR/manifest.json"
    UPDATED=$(jq --arg path "$PARSED_PATH" --arg mod "$(today_iso)" '
      .cookbook_projects += [$path] | .cookbook_projects |= unique | .modified = $mod
    ' "$MANIFEST")
    echo "$UPDATED" > "$MANIFEST"

    json_build project="$PARSED_PROJECT" cookbook_project="$PARSED_PATH"
    ;;

  unlink-cookbook)
    require_flag "project" "$PARSED_PROJECT"
    require_flag "path" "$PARSED_PATH"
    DIR="$(require_project "$PARSED_PROJECT")"

    MANIFEST="$DIR/manifest.json"
    UPDATED=$(jq --arg path "$PARSED_PATH" --arg mod "$(today_iso)" '
      .cookbook_projects -= [$path] | .modified = $mod
    ' "$MANIFEST")
    echo "$UPDATED" > "$MANIFEST"

    json_build project="$PARSED_PROJECT" cookbook_project="$PARSED_PATH"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: project.sh <init|status|link-cookbook|unlink-cookbook> [flags]" >&2
    exit 1
    ;;
esac
