#!/bin/bash
# assign-specialists.sh — Determine specialist assignment for a recipe
# Usage: assign-specialists.sh <recipe-path> [--platforms '<json-array>'] [--tier-order]
# Outputs: Newline-separated specialist domains to stdout
# With --tier-order: output is sorted by build tier

set -euo pipefail

RECIPE_PATH="$1"; shift
PLATFORMS_JSON="[]"
TIER_ORDER=false
MAPPING="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/docs/research/specialist-assignment.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms) PLATFORMS_JSON="$2"; shift 2 ;;
    --tier-order) TIER_ORDER=true; shift ;;
    *) shift ;;
  esac
done

SPECIALISTS=()

# 1. Category mapping — extract category from recipe scope in frontmatter
RECIPE_DOMAIN=$(awk '/^---$/{ if (++n==2) exit } /^domain: / && n==1 { sub(/^domain: .*recipes\//, ""); sub(/\/[^\/]*$/, ""); gsub(/\//, "."); print }' "$RECIPE_PATH")

if [[ -n "$RECIPE_DOMAIN" ]]; then
  CATEGORY="recipe.$(echo "$RECIPE_DOMAIN" | cut -d. -f1)"

  CATEGORY_SPECIALISTS=$(jq -r --arg cat "$CATEGORY" '
    .["category-mappings"] | to_entries[] |
    select($cat | startswith(.key)) |
    .value[]' "$MAPPING" 2>/dev/null || true)

  for s in $CATEGORY_SPECIALISTS; do
    SPECIALISTS+=("$s")
  done
fi

# 2. Content keyword scan
RECIPE_CONTENT=$(cat "$RECIPE_PATH")

while IFS= read -r keyword; do
  if echo "$RECIPE_CONTENT" | grep -qi "$keyword"; then
    SPECIALIST=$(jq -r --arg kw "$keyword" '.["content-keywords"][$kw]' "$MAPPING")
    if [[ "$SPECIALIST" != "null" && -n "$SPECIALIST" ]]; then
      SPECIALISTS+=("$SPECIALIST")
    fi
  fi
done < <(jq -r '.["content-keywords"] | keys[]' "$MAPPING")

# 3. Platform specialists
while IFS= read -r plat; do
  while IFS= read -r s; do
    if [[ -n "$s" && "$s" != "null" ]]; then
      SPECIALISTS+=("$s")
    fi
  done < <(jq -r --arg p "$plat" '.["platform-mappings"][$p] // [] | .[]' "$MAPPING")
done < <(echo "$PLATFORMS_JSON" | jq -r '.[]')

# Deduplicate and limit
if [[ ${#SPECIALISTS[@]} -eq 0 ]]; then
  exit 0
fi

UNIQUE=$(printf '%s\n' "${SPECIALISTS[@]}" | sort -u)

# Apply tier ordering if requested
if $TIER_ORDER; then
  echo "$UNIQUE" | while IFS= read -r spec; do
    [[ -z "$spec" ]] && continue
    INDEX=$(jq -r --arg s "$spec" '.["tier-order"] | to_entries[] | select(.value == $s) | .key' "$MAPPING")
    echo "${INDEX:-999} $spec"
  done | sort -n | awk '{print $2}'
else
  echo "$UNIQUE"
fi
