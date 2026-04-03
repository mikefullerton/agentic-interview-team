#!/bin/bash
# db-artifact.sh — Write or query artifacts (stores full file content)
# Usage: db-artifact.sh write --project <id> [--run <id>] [--agent-run <id>] --path <path> --category <cat> [--specialist <domain>]
#        db-artifact.sh get --id <id>
#        db-artifact.sh search --project <id> [--category <cat>] [--specialist <domain>] [--text <search>]

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="${1:-}"; shift || true
PROJECT_ID=""
RUN_ID=""
AGENT_RUN_ID=""
FILE_PATH=""
CATEGORY=""
SPECIALIST=""
ARTIFACT_ID=""
SEARCH_TEXT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --run) RUN_ID="$2"; shift 2 ;;
    --agent-run) AGENT_RUN_ID="$2"; shift 2 ;;
    --path) FILE_PATH="$2"; shift 2 ;;
    --category) CATEGORY="$2"; shift 2 ;;
    --specialist) SPECIALIST="$2"; shift 2 ;;
    --id) ARTIFACT_ID="$2"; shift 2 ;;
    --text) SEARCH_TEXT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  write)
    if [[ ! -f "$FILE_PATH" ]]; then
      echo "File not found: $FILE_PATH" >&2
      exit 1
    fi

    HASH=$(shasum -a 256 "$FILE_PATH" | awk '{print $1}')
    TITLE=$(awk '/^---$/{ if (++n==2) exit } /^title: / && n==1 { sub(/^title: "?/, ""); sub(/"?$/, ""); print }' "$FILE_PATH")
    FRONTMATTER=$(awk '/^---$/{ if (++n==2) exit; next } n==1 { print }' "$FILE_PATH" | python3 -c "
import sys, json
fm = {}
for line in sys.stdin:
    line = line.strip()
    if ':' in line:
        k, v = line.split(':', 1)
        v = v.strip().strip('\"')
        fm[k.strip()] = v
print(json.dumps(fm))
" 2>/dev/null || echo "{}")
    CONTENT=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$FILE_PATH")
    REL_PATH=$(basename "$FILE_PATH")

    RUN_VAL="NULL"; [[ -n "$RUN_ID" ]] && RUN_VAL="$RUN_ID"
    AR_VAL="NULL"; [[ -n "$AGENT_RUN_ID" ]] && AR_VAL="$AGENT_RUN_ID"
    SPEC_VAL="NULL"; [[ -n "$SPECIALIST" ]] && SPEC_VAL="'$SPECIALIST'"

    EXISTING=$(sqlite3 "$DB_PATH" "SELECT id, version FROM artifacts WHERE path='${FILE_PATH//\'/\'\'}' AND project_id=$PROJECT_ID ORDER BY version DESC LIMIT 1" 2>/dev/null || echo "")

    TMPFILE=$(mktemp)
    printf '%s' "$CONTENT" > "$TMPFILE"

    if [[ -n "$EXISTING" ]]; then
      OLD_ID=$(echo "$EXISTING" | cut -d'|' -f1)
      OLD_VERSION=$(echo "$EXISTING" | cut -d'|' -f2)
      NEW_VERSION=$((OLD_VERSION + 1))
      sqlite3 "$DB_PATH" "UPDATE artifacts SET content=readfile('$TMPFILE'), content_hash='$HASH', version=$NEW_VERSION, modified=CURRENT_TIMESTAMP, frontmatter_json='${FRONTMATTER//\'/\'\'}', title='${TITLE//\'/\'\'}' WHERE id=$OLD_ID"
      rm -f "$TMPFILE"
      echo "{\"id\": $OLD_ID, \"version\": $NEW_VERSION}"
    else
      sqlite3 "$DB_PATH" "INSERT INTO artifacts (project_id, workflow_run_id, agent_run_id, path, relative_path, category, title, specialist, frontmatter_json, content, content_hash) VALUES ($PROJECT_ID, $RUN_VAL, $AR_VAL, '${FILE_PATH//\'/\'\'}', '$REL_PATH', '$CATEGORY', '${TITLE//\'/\'\'}', $SPEC_VAL, '${FRONTMATTER//\'/\'\'}', readfile('$TMPFILE'), '$HASH'); SELECT last_insert_rowid();" | tail -1 | awk '{print "{\"id\": "$1"}"}'
      rm -f "$TMPFILE"
    fi
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM artifacts WHERE id=$ARTIFACT_ID"
    ;;
  search)
    WHERE="project_id=$PROJECT_ID"
    [[ -n "$CATEGORY" ]] && WHERE="$WHERE AND category='$CATEGORY'"
    [[ -n "$SPECIALIST" ]] && WHERE="$WHERE AND specialist='$SPECIALIST'"
    [[ -n "$SEARCH_TEXT" ]] && WHERE="$WHERE AND content LIKE '%${SEARCH_TEXT//\'/\'\'}%'"
    sqlite3 -json "$DB_PATH" "SELECT id, project_id, path, category, title, specialist, version, created, modified FROM artifacts WHERE $WHERE ORDER BY modified DESC"
    ;;
  *)
    echo "Usage: db-artifact.sh write|get|search [options]" >&2
    exit 1
    ;;
esac
