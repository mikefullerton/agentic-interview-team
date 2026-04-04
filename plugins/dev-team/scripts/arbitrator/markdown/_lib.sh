#!/bin/bash
# _lib.sh — Shared helpers for the markdown arbitrator backend

SESSION_BASE="${ARBITRATOR_SESSION_BASE:-${HOME}/.agentic-cookbook/dev-team/sessions}"

# Generate a new session ID (human-readable, sortable, collision-resistant)
new_session_id() {
  printf '%s-%04x' "$(date +%Y%m%d-%H%M%S)" $((RANDOM % 65536))
}

# Get session directory path
session_dir() {
  local session_id="$1"
  echo "${SESSION_BASE}/${session_id}"
}

# Require a session directory exists
require_session() {
  local session_id="$1"
  local dir
  dir="$(session_dir "$session_id")"
  if [[ ! -d "$dir" ]]; then
    echo "Session not found: ${session_id}" >&2
    exit 1
  fi
  echo "$dir"
}

# Get next sequence number for a directory
next_seq() {
  local dir="$1"
  mkdir -p "$dir"
  local count
  count=$(find "$dir" -maxdepth 1 -name '*.json' -o -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' ')
  printf '%04d' $((count + 1))
}

# Slug a string for filenames
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | sed 's/^-//;s/-$//' | cut -c1-40
}

# ISO 8601 timestamp
now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ
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

# Parse common flags from arguments, setting variables in the caller's scope
# Usage: parse_flags "$@" and then check PARSED_SESSION, PARSED_SPECIALIST, etc.
parse_flags() {
  PARSED_SESSION=""
  PARSED_SPECIALIST=""
  PARSED_TYPE=""
  PARSED_STATE=""
  PARSED_CHANGED_BY=""
  PARSED_DESCRIPTION=""
  PARSED_CONTENT=""
  PARSED_CATEGORY=""
  PARSED_SEVERITY=""
  PARSED_TITLE=""
  PARSED_DETAIL=""
  PARSED_PLAYBOOK=""
  PARSED_TEAM_LEAD=""
  PARSED_USER=""
  PARSED_MACHINE=""
  PARSED_PATH=""
  PARSED_RESULT=""
  PARSED_FINDING=""
  PARSED_MESSAGE=""
  PARSED_ARTIFACT=""
  PARSED_INTERPRETATION=""
  PARSED_OPTION_TEXT=""
  PARSED_IS_DEFAULT=""
  PARSED_SORT_ORDER=""
  PARSED_REASON=""
  PARSED_STATUS=""
  PARSED_TEAM=""
  PARSED_ITERATION=""
  PARSED_VERIFIER_FEEDBACK=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --session) PARSED_SESSION="$2"; shift 2 ;;
      --specialist) PARSED_SPECIALIST="$2"; shift 2 ;;
      --type) PARSED_TYPE="$2"; shift 2 ;;
      --state) PARSED_STATE="$2"; shift 2 ;;
      --changed-by) PARSED_CHANGED_BY="$2"; shift 2 ;;
      --description) PARSED_DESCRIPTION="$2"; shift 2 ;;
      --content) PARSED_CONTENT="$2"; shift 2 ;;
      --category) PARSED_CATEGORY="$2"; shift 2 ;;
      --severity) PARSED_SEVERITY="$2"; shift 2 ;;
      --title) PARSED_TITLE="$2"; shift 2 ;;
      --detail) PARSED_DETAIL="$2"; shift 2 ;;
      --playbook) PARSED_PLAYBOOK="$2"; shift 2 ;;
      --team-lead) PARSED_TEAM_LEAD="$2"; shift 2 ;;
      --user) PARSED_USER="$2"; shift 2 ;;
      --machine) PARSED_MACHINE="$2"; shift 2 ;;
      --path) PARSED_PATH="$2"; shift 2 ;;
      --result) PARSED_RESULT="$2"; shift 2 ;;
      --finding) PARSED_FINDING="$2"; shift 2 ;;
      --message) PARSED_MESSAGE="$2"; shift 2 ;;
      --artifact) PARSED_ARTIFACT="$2"; shift 2 ;;
      --interpretation) PARSED_INTERPRETATION="$2"; shift 2 ;;
      --option-text) PARSED_OPTION_TEXT="$2"; shift 2 ;;
      --is-default) PARSED_IS_DEFAULT="$2"; shift 2 ;;
      --sort-order) PARSED_SORT_ORDER="$2"; shift 2 ;;
      --reason) PARSED_REASON="$2"; shift 2 ;;
      --status) PARSED_STATUS="$2"; shift 2 ;;
      --team) PARSED_TEAM="$2"; shift 2 ;;
      --iteration) PARSED_ITERATION="$2"; shift 2 ;;
      --verifier-feedback) PARSED_VERIFIER_FEEDBACK="$2"; shift 2 ;;
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
