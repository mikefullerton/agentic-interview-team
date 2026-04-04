#!/bin/bash
# _lib.sh — Shared helpers for the markdown project-storage backend

PROJECT_DIR_NAME=".dev-team-project"

# ISO 8601 date
today_iso() {
  date -u +%Y-%m-%d
}

# ISO 8601 timestamp
now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

# Slug a string for filenames
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/^-//;s/-$//' | cut -c1-40
}

# Get the .dev-team-project directory for a project path
project_dir() {
  local project_path="$1"
  echo "${project_path}/${PROJECT_DIR_NAME}"
}

# Require a project directory exists
require_project() {
  local project_path="$1"
  local dir
  dir="$(project_dir "$project_path")"
  if [[ ! -d "$dir" ]]; then
    echo "No dev-team project at: ${project_path}" >&2
    exit 1
  fi
  echo "$dir"
}

# Generate next ID for a type in a directory
# Returns e.g., "todo-0001"
next_id() {
  local type="$1"
  local dir="$2"
  mkdir -p "$dir"
  local count
  count=$(find "$dir" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  printf '%s-%04d' "$type" $((count + 1))
}

# Read YAML frontmatter from a markdown file as JSON
# Expects --- delimited frontmatter
read_frontmatter() {
  local file="$1"
  local in_frontmatter=false
  local yaml=""

  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if $in_frontmatter; then
        break
      else
        in_frontmatter=true
        continue
      fi
    fi
    if $in_frontmatter; then
      yaml+="${line}"$'\n'
    fi
  done < "$file"

  # Convert simple YAML key: value pairs to JSON
  # Handles: strings, nulls, arrays (as comma-separated in brackets)
  echo "$yaml" | awk '
    BEGIN { print "{"; first=1 }
    /^[a-zA-Z_][a-zA-Z0-9_]*:/ {
      key = $0
      sub(/:.*/, "", key)
      val = $0
      sub(/^[^:]*: */, "", val)

      # Remove trailing whitespace
      gsub(/[[:space:]]+$/, "", val)

      if (!first) printf ",\n"
      first = 0

      if (val == "null" || val == "") {
        printf "  \"%s\": null", key
      } else if (val ~ /^\[.*\]$/) {
        # Array value — parse comma-separated items
        inner = val
        gsub(/^\[|\]$/, "", inner)
        printf "  \"%s\": [", key
        n = split(inner, items, ",")
        for (i = 1; i <= n; i++) {
          gsub(/^ +| +$/, "", items[i])
          if (i > 1) printf ", "
          printf "\"%s\"", items[i]
        }
        printf "]"
      } else {
        # String value — escape quotes
        gsub(/"/, "\\\"", val)
        printf "  \"%s\": \"%s\"", key, val
      }
    }
    END { printf "\n}\n" }
  '
}

# Read the body (everything after frontmatter) from a markdown file
read_body() {
  local file="$1"
  local past_frontmatter=false
  local found_first=false

  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if $found_first; then
        past_frontmatter=true
        continue
      else
        found_first=true
        continue
      fi
    fi
    if $past_frontmatter; then
      echo "$line"
    fi
  done < "$file"
}

# Write a markdown file with YAML frontmatter
# Args: file, body (reads frontmatter fields from stdin as JSON)
write_item() {
  local file="$1"
  local body="$2"
  local json="$3"

  {
    echo "---"
    echo "$json" | jq -r 'to_entries[] | "\(.key): \(.value // "null")"'
    echo "---"
    echo ""
    echo "$body"
  } > "$file"
}

# Update specific frontmatter fields in a file
# Args: file, json with fields to update
update_item() {
  local file="$1"
  local updates="$2"

  local current_json
  current_json=$(read_frontmatter "$file")
  local body
  body=$(read_body "$file")

  # Merge updates into current, update modified date
  local merged
  merged=$(echo "$current_json" | jq --argjson updates "$updates" --arg mod "$(today_iso)" '
    . + $updates + {modified: $mod}
  ')

  write_item "$file" "$body" "$merged"
}

# Build a JSON object from key=value pairs using jq
json_build() {
  local args=()
  for pair in "$@"; do
    local key="${pair%%=*}"
    local val="${pair#*=}"
    args+=(--arg "$key" "$val")
  done
  jq -n "${args[@]}" '$ARGS.named'
}

# Parse common flags from arguments
parse_flags() {
  PARSED_PROJECT=""
  PARSED_NAME=""
  PARSED_DESCRIPTION=""
  PARSED_PATH=""
  PARSED_ID=""
  PARSED_TITLE=""
  PARSED_STATUS=""
  PARSED_PRIORITY=""
  PARSED_SEVERITY=""
  PARSED_ASSIGNEE=""
  PARSED_MILESTONE=""
  PARSED_BLOCKED_BY=""
  PARSED_TARGET_DATE=""
  PARSED_DEPENDENCIES=""
  PARSED_SOURCE=""
  PARSED_RELATED_FINDINGS=""
  PARSED_RAISED_BY=""
  PARSED_RELATED_TO=""
  PARSED_TYPE=""
  PARSED_RATIONALE=""
  PARSED_ALTERNATIVES=""
  PARSED_MADE_BY=""
  PARSED_DATE=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project) PARSED_PROJECT="$2"; shift 2 ;;
      --name) PARSED_NAME="$2"; shift 2 ;;
      --description) PARSED_DESCRIPTION="$2"; shift 2 ;;
      --path) PARSED_PATH="$2"; shift 2 ;;
      --id) PARSED_ID="$2"; shift 2 ;;
      --title) PARSED_TITLE="$2"; shift 2 ;;
      --status) PARSED_STATUS="$2"; shift 2 ;;
      --priority) PARSED_PRIORITY="$2"; shift 2 ;;
      --severity) PARSED_SEVERITY="$2"; shift 2 ;;
      --assignee) PARSED_ASSIGNEE="$2"; shift 2 ;;
      --milestone) PARSED_MILESTONE="$2"; shift 2 ;;
      --blocked-by) PARSED_BLOCKED_BY="$2"; shift 2 ;;
      --target-date) PARSED_TARGET_DATE="$2"; shift 2 ;;
      --dependencies) PARSED_DEPENDENCIES="$2"; shift 2 ;;
      --source) PARSED_SOURCE="$2"; shift 2 ;;
      --related-findings) PARSED_RELATED_FINDINGS="$2"; shift 2 ;;
      --raised-by) PARSED_RAISED_BY="$2"; shift 2 ;;
      --related-to) PARSED_RELATED_TO="$2"; shift 2 ;;
      --type) PARSED_TYPE="$2"; shift 2 ;;
      --rationale) PARSED_RATIONALE="$2"; shift 2 ;;
      --alternatives) PARSED_ALTERNATIVES="$2"; shift 2 ;;
      --made-by) PARSED_MADE_BY="$2"; shift 2 ;;
      --date) PARSED_DATE="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
}

# Require a parsed flag is non-empty
require_flag() {
  local name="$1" value="$2"
  if [[ -z "$value" ]]; then
    echo "Missing required flag: --${name}" >&2
    exit 1
  fi
}
