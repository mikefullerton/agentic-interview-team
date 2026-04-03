# Shared Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SQLite shared database to the dev-team plugin with shell script API, enabling cross-workflow resumability, cross-project insights, and agent activity logging.

**Architecture:** SQLite DB at `~/.agentic-cookbook/dev-team/dev-team.db`. Shell scripts in `scripts/db/` wrap all DB operations. Workflows call scripts to log runs, agents, findings, and artifacts. Agents receive run/project IDs and call scripts for their own logging.

**Tech Stack:** SQLite3 CLI, bash shell scripts, jq for JSON output.

---

## File Structure

### New files

```
scripts/db/
  db-init.sh              # Create/migrate schema (idempotent)
  db-project.sh           # CRUD for projects table
  db-run.sh               # Start/complete workflow runs
  db-agent.sh             # Start/complete agent runs
  db-finding.sh           # Record and update findings
  db-artifact.sh          # Write/query artifacts with full content
  db-message.sh           # Log agent activity messages
  db-query.sh             # Generic SQL query (JSON or table output)
  db-cleanup.sh           # Age out old runs
  schema.sql              # Full schema DDL (sourced by db-init.sh)
```

### Modified files

```
skills/dev-team/SKILL.md                              # Add db-init.sh call to startup
skills/dev-team/workflows/interview.md                # Add DB logging
skills/dev-team/workflows/create-project-from-code.md # Add DB logging + resumability
skills/dev-team/workflows/generate.md                 # Add DB logging + read previous findings
skills/dev-team/workflows/create-code-from-project.md # Add DB logging + resumability
skills/dev-team/workflows/lint.md                     # Add DB logging + trend queries
skills/dev-team/workflows/compare-code.md             # Add DB logging + comparison tracking
skills/dev-team/workflows/view-project.md             # Read from DB for enriched view
.claude/CLAUDE.md                                     # Document DB location and scripts
```

---

## Execution Strategy

Per the optimize-subagent-dispatch rule:
- **Tasks 1-2** (schema + scripts): Mechanical — exact code in plan. Fast model, parallel.
- **Task 3** (workflow integration): Judgment — how to weave DB calls into each workflow. Full model.
- **Task 4** (router + docs): Mechanical edits. Fast model.

---

## Task 1: Create schema and db-init.sh

**Files:**
- Create: `scripts/db/schema.sql`
- Create: `scripts/db/db-init.sh`

- [ ] **Step 1:** Create `scripts/db/schema.sql`:

```sql
-- Dev-team shared database schema v1

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  workflow TEXT NOT NULL,
  status TEXT DEFAULT 'running',
  started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_run_id INTEGER NOT NULL REFERENCES workflow_runs(id),
  agent_type TEXT NOT NULL,
  specialist_domain TEXT,
  status TEXT DEFAULT 'running',
  started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed TIMESTAMP,
  output_path TEXT
);

CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_run_id INTEGER REFERENCES agent_runs(id),
  project_id INTEGER NOT NULL REFERENCES projects(id),
  type TEXT NOT NULL,
  severity TEXT,
  description TEXT NOT NULL,
  artifact_path TEXT,
  status TEXT DEFAULT 'open',
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requirements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  recipe_path TEXT NOT NULL,
  text TEXT NOT NULL,
  keyword TEXT NOT NULL,
  covered_by_baseline TEXT,
  covered_by_target TEXT
);

CREATE TABLE IF NOT EXISTS comparisons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  workflow_run_id INTEGER REFERENCES workflow_runs(id),
  baseline_path TEXT NOT NULL,
  target_path TEXT NOT NULL,
  preservation_pct REAL,
  regressions_count INTEGER DEFAULT 0,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS specialist_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  workflow_run_id INTEGER REFERENCES workflow_runs(id),
  recipe_path TEXT NOT NULL,
  specialist TEXT NOT NULL,
  tier INTEGER,
  approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS screenshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  comparison_id INTEGER NOT NULL REFERENCES comparisons(id),
  name TEXT NOT NULL,
  similarity_pct REAL,
  baseline_path TEXT,
  target_path TEXT,
  diff_path TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  workflow_run_id INTEGER REFERENCES workflow_runs(id),
  agent_run_id INTEGER REFERENCES agent_runs(id),
  path TEXT,
  relative_path TEXT,
  category TEXT NOT NULL,
  title TEXT,
  specialist TEXT,
  frontmatter_json TEXT,
  content TEXT,
  content_hash TEXT,
  version INTEGER DEFAULT 1,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_run_id INTEGER REFERENCES workflow_runs(id),
  agent_run_id INTEGER REFERENCES agent_runs(id),
  agent_type TEXT,
  specialist_domain TEXT,
  persona TEXT,
  message TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_workflow_runs_project ON workflow_runs(project_id, workflow);
CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow ON agent_runs(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_findings_project ON findings(project_id, type, status);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id, category);
CREATE INDEX IF NOT EXISTS idx_messages_run ON messages(workflow_run_id);
```

- [ ] **Step 2:** Create `scripts/db/db-init.sh`:

```bash
#!/bin/bash
# db-init.sh — Create or migrate the dev-team shared database
# Usage: db-init.sh
# Idempotent — safe to call on every workflow startup

set -euo pipefail

DB_DIR="${HOME}/.agentic-cookbook/dev-team"
DB_PATH="${DB_DIR}/dev-team.db"
SCHEMA_PATH="$(dirname "$0")/schema.sql"
SCHEMA_VERSION="1"

mkdir -p "$DB_DIR"

# Apply schema (all CREATE IF NOT EXISTS — idempotent)
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"

# Check/set schema version
CURRENT_VERSION=$(sqlite3 "$DB_PATH" "SELECT value FROM meta WHERE key='schema_version'" 2>/dev/null || echo "")

if [[ -z "$CURRENT_VERSION" ]]; then
  sqlite3 "$DB_PATH" "INSERT INTO meta (key, value) VALUES ('schema_version', '$SCHEMA_VERSION')"
elif [[ "$CURRENT_VERSION" != "$SCHEMA_VERSION" ]]; then
  # Future: run migration scripts here
  # For now, just update version (schema uses IF NOT EXISTS so new tables are added safely)
  sqlite3 "$DB_PATH" "UPDATE meta SET value='$SCHEMA_VERSION' WHERE key='schema_version'"
  echo "Migrated database schema from v${CURRENT_VERSION} to v${SCHEMA_VERSION}" >&2
fi

echo "$DB_PATH"
```

- [ ] **Step 3:** Make executable and commit:

```bash
chmod +x scripts/db/db-init.sh
git add scripts/db/schema.sql scripts/db/db-init.sh
git commit -m "Add database schema and init script (10 tables, v1)"
git push
```

---

## Task 2: Create all DB shell scripts

**Files:**
- Create: `scripts/db/db-project.sh`
- Create: `scripts/db/db-run.sh`
- Create: `scripts/db/db-agent.sh`
- Create: `scripts/db/db-finding.sh`
- Create: `scripts/db/db-artifact.sh`
- Create: `scripts/db/db-message.sh`
- Create: `scripts/db/db-query.sh`
- Create: `scripts/db/db-cleanup.sh`

- [ ] **Step 1:** Create `scripts/db/db-project.sh`:

```bash
#!/bin/bash
# db-project.sh — Create or get a project
# Usage: db-project.sh --name <name> --path <path>
#        db-project.sh --get <id>
#        db-project.sh --list
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION=""
NAME=""
PROJECT_PATH=""
ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; ACTION="upsert"; shift 2 ;;
    --path) PROJECT_PATH="$2"; shift 2 ;;
    --get) ID="$2"; ACTION="get"; shift 2 ;;
    --list) ACTION="list"; shift ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  upsert)
    # Try to find existing project by name
    EXISTING=$(sqlite3 "$DB_PATH" "SELECT id FROM projects WHERE name='${NAME//\'/\'\'}' LIMIT 1" 2>/dev/null || echo "")
    if [[ -n "$EXISTING" ]]; then
      sqlite3 "$DB_PATH" "UPDATE projects SET path='${PROJECT_PATH//\'/\'\'}', modified=CURRENT_TIMESTAMP WHERE id=$EXISTING"
      echo "{\"id\": $EXISTING}"
    else
      sqlite3 "$DB_PATH" "INSERT INTO projects (name, path) VALUES ('${NAME//\'/\'\'}', '${PROJECT_PATH//\'/\'\'}') RETURNING id" | awk '{print "{\"id\": "$1"}"}'
    fi
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM projects WHERE id=$ID"
    ;;
  list)
    sqlite3 -json "$DB_PATH" "SELECT * FROM projects ORDER BY modified DESC"
    ;;
  *)
    echo "Usage: db-project.sh --name <name> --path <path> | --get <id> | --list" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 2:** Create `scripts/db/db-run.sh`:

```bash
#!/bin/bash
# db-run.sh — Start or complete a workflow run
# Usage: db-run.sh start --project <id> --workflow <name>
#        db-run.sh complete --id <id> --status <completed|failed|interrupted>
#        db-run.sh --get <id>
#        db-run.sh --latest --project <id> --workflow <name>
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="$1"; shift
PROJECT_ID=""
WORKFLOW=""
RUN_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    --id) RUN_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --get) RUN_ID="$2"; ACTION="get"; shift 2 ;;
    --latest) ACTION="latest"; shift ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    sqlite3 "$DB_PATH" "INSERT INTO workflow_runs (project_id, workflow) VALUES ($PROJECT_ID, '$WORKFLOW') RETURNING id" | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    sqlite3 "$DB_PATH" "UPDATE workflow_runs SET status='$STATUS', completed=CURRENT_TIMESTAMP WHERE id=$RUN_ID"
    echo "{\"id\": $RUN_ID, \"status\": \"$STATUS\"}"
    ;;
  get)
    sqlite3 -json "$DB_PATH" "SELECT * FROM workflow_runs WHERE id=$RUN_ID"
    ;;
  latest)
    sqlite3 -json "$DB_PATH" "SELECT * FROM workflow_runs WHERE project_id=$PROJECT_ID AND workflow='$WORKFLOW' ORDER BY started DESC LIMIT 1"
    ;;
  *)
    echo "Usage: db-run.sh start|complete|--get|--latest [options]" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 3:** Create `scripts/db/db-agent.sh`:

```bash
#!/bin/bash
# db-agent.sh — Start or complete an agent run
# Usage: db-agent.sh start --run <id> --agent <type> [--specialist <domain>]
#        db-agent.sh complete --id <id> --status <completed|failed> [--output-path <path>]
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="$1"; shift
RUN_ID=""
AGENT_TYPE=""
SPECIALIST=""
AGENT_ID=""
STATUS=""
OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run) RUN_ID="$2"; shift 2 ;;
    --agent) AGENT_TYPE="$2"; shift 2 ;;
    --specialist) SPECIALIST="$2"; shift 2 ;;
    --id) AGENT_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --output-path) OUTPUT_PATH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  start)
    SPEC_SQL=""
    if [[ -n "$SPECIALIST" ]]; then
      SPEC_SQL=", specialist_domain='$SPECIALIST'"
    fi
    sqlite3 "$DB_PATH" "INSERT INTO agent_runs (workflow_run_id, agent_type, specialist_domain) VALUES ($RUN_ID, '$AGENT_TYPE', $(if [[ -n "$SPECIALIST" ]]; then echo "'$SPECIALIST'"; else echo "NULL"; fi)) RETURNING id" | awk '{print "{\"id\": "$1"}"}'
    ;;
  complete)
    OUT_SQL=""
    if [[ -n "$OUTPUT_PATH" ]]; then
      OUT_SQL=", output_path='${OUTPUT_PATH//\'/\'\'}'"
    fi
    sqlite3 "$DB_PATH" "UPDATE agent_runs SET status='$STATUS', completed=CURRENT_TIMESTAMP${OUT_SQL} WHERE id=$AGENT_ID"
    echo "{\"id\": $AGENT_ID, \"status\": \"$STATUS\"}"
    ;;
  *)
    echo "Usage: db-agent.sh start|complete [options]" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 4:** Create `scripts/db/db-finding.sh`:

```bash
#!/bin/bash
# db-finding.sh — Record or update a finding
# Usage: db-finding.sh --agent-run <id> --project <id> --type <type> --severity <sev> --description "<text>" [--artifact-path <path>]
#        db-finding.sh update --id <id> --status <accepted|rejected|fixed>
#        db-finding.sh --list --project <id> [--type <type>] [--status <status>]
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="create"
AGENT_RUN_ID=""
PROJECT_ID=""
TYPE=""
SEVERITY=""
DESCRIPTION=""
ARTIFACT_PATH=""
FINDING_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    update) ACTION="update"; shift ;;
    --list) ACTION="list"; shift ;;
    --agent-run) AGENT_RUN_ID="$2"; shift 2 ;;
    --project) PROJECT_ID="$2"; shift 2 ;;
    --type) TYPE="$2"; shift 2 ;;
    --severity) SEVERITY="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    --artifact-path) ARTIFACT_PATH="$2"; shift 2 ;;
    --id) FINDING_ID="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$ACTION" in
  create)
    sqlite3 "$DB_PATH" "INSERT INTO findings (agent_run_id, project_id, type, severity, description, artifact_path) VALUES ($(if [[ -n "$AGENT_RUN_ID" ]]; then echo "$AGENT_RUN_ID"; else echo "NULL"; fi), $PROJECT_ID, '$TYPE', $(if [[ -n "$SEVERITY" ]]; then echo "'$SEVERITY'"; else echo "NULL"; fi), '${DESCRIPTION//\'/\'\'}', $(if [[ -n "$ARTIFACT_PATH" ]]; then echo "'${ARTIFACT_PATH//\'/\'\'}'"; else echo "NULL"; fi)) RETURNING id" | awk '{print "{\"id\": "$1"}"}'
    ;;
  update)
    sqlite3 "$DB_PATH" "UPDATE findings SET status='$STATUS' WHERE id=$FINDING_ID"
    echo "{\"id\": $FINDING_ID, \"status\": \"$STATUS\"}"
    ;;
  list)
    WHERE="project_id=$PROJECT_ID"
    [[ -n "$TYPE" ]] && WHERE="$WHERE AND type='$TYPE'"
    [[ -n "$STATUS" ]] && WHERE="$WHERE AND status='$STATUS'"
    sqlite3 -json "$DB_PATH" "SELECT * FROM findings WHERE $WHERE ORDER BY created DESC"
    ;;
  *)
    echo "Usage: db-finding.sh [create|update|--list] [options]" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 5:** Create `scripts/db/db-artifact.sh`:

```bash
#!/bin/bash
# db-artifact.sh — Write or query artifacts (stores full file content)
# Usage: db-artifact.sh write --project <id> [--run <id>] [--agent-run <id>] --path <path> --category <cat> [--specialist <domain>]
#        db-artifact.sh get --id <id>
#        db-artifact.sh search --project <id> [--category <cat>] [--specialist <domain>] [--text <search>]
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

ACTION="$1"; shift
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

    # Compute hash
    HASH=$(shasum -a 256 "$FILE_PATH" | awk '{print $1}')

    # Extract title from frontmatter
    TITLE=$(awk '/^---$/{ if (++n==2) exit } /^title: / && n==1 { sub(/^title: "?/, ""); sub(/"?$/, ""); print }' "$FILE_PATH")

    # Extract frontmatter as JSON (simple: key-value pairs)
    FRONTMATTER=$(awk '/^---$/{ if (++n==2) exit; next } n==1 { print }' "$FILE_PATH" | python3 -c "
import sys, json, re
fm = {}
for line in sys.stdin:
    line = line.strip()
    if ':' in line:
        k, v = line.split(':', 1)
        v = v.strip().strip('\"')
        fm[k.strip()] = v
print(json.dumps(fm))
" 2>/dev/null || echo "{}")

    # Extract content (everything after second ---)
    CONTENT=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$FILE_PATH")

    # Compute relative path
    REL_PATH=$(basename "$FILE_PATH")

    # Check for existing artifact with same path
    EXISTING=$(sqlite3 "$DB_PATH" "SELECT id, version FROM artifacts WHERE path='${FILE_PATH//\'/\'\'}' AND project_id=$PROJECT_ID ORDER BY version DESC LIMIT 1" 2>/dev/null || echo "")

    if [[ -n "$EXISTING" ]]; then
      OLD_ID=$(echo "$EXISTING" | cut -d'|' -f1)
      OLD_VERSION=$(echo "$EXISTING" | cut -d'|' -f2)
      NEW_VERSION=$((OLD_VERSION + 1))
      # Use a temp file for content to handle special characters
      TMPFILE=$(mktemp)
      echo "$CONTENT" > "$TMPFILE"
      sqlite3 "$DB_PATH" "UPDATE artifacts SET content=readfile('$TMPFILE'), content_hash='$HASH', version=$NEW_VERSION, modified=CURRENT_TIMESTAMP, frontmatter_json='${FRONTMATTER//\'/\'\'}', title='${TITLE//\'/\'\'}' WHERE id=$OLD_ID"
      rm -f "$TMPFILE"
      echo "{\"id\": $OLD_ID, \"version\": $NEW_VERSION}"
    else
      TMPFILE=$(mktemp)
      echo "$CONTENT" > "$TMPFILE"
      sqlite3 "$DB_PATH" "INSERT INTO artifacts (project_id, workflow_run_id, agent_run_id, path, relative_path, category, title, specialist, frontmatter_json, content, content_hash) VALUES ($PROJECT_ID, $(if [[ -n "$RUN_ID" ]]; then echo "$RUN_ID"; else echo "NULL"; fi), $(if [[ -n "$AGENT_RUN_ID" ]]; then echo "$AGENT_RUN_ID"; else echo "NULL"; fi), '${FILE_PATH//\'/\'\'}', '$REL_PATH', '$CATEGORY', '${TITLE//\'/\'\'}', $(if [[ -n "$SPECIALIST" ]]; then echo "'$SPECIALIST'"; else echo "NULL"; fi), '${FRONTMATTER//\'/\'\'}', readfile('$TMPFILE'), '$HASH') RETURNING id" | awk '{print "{\"id\": "$1"}"}'
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
```

- [ ] **Step 6:** Create `scripts/db/db-message.sh`:

```bash
#!/bin/bash
# db-message.sh — Log an agent activity message
# Usage: db-message.sh --run <id> [--agent-run <id>] [--agent-type <type>] [--specialist <domain>] [--persona <name>] --message "<text>"
# Output: JSON to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

RUN_ID=""
AGENT_RUN_ID=""
AGENT_TYPE=""
SPECIALIST=""
PERSONA=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run) RUN_ID="$2"; shift 2 ;;
    --agent-run) AGENT_RUN_ID="$2"; shift 2 ;;
    --agent-type) AGENT_TYPE="$2"; shift 2 ;;
    --specialist) SPECIALIST="$2"; shift 2 ;;
    --persona) PERSONA="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$MESSAGE" ]]; then
  echo "Usage: db-message.sh --run <id> --message \"<text>\"" >&2
  exit 1
fi

sqlite3 "$DB_PATH" "INSERT INTO messages (workflow_run_id, agent_run_id, agent_type, specialist_domain, persona, message) VALUES ($(if [[ -n "$RUN_ID" ]]; then echo "$RUN_ID"; else echo "NULL"; fi), $(if [[ -n "$AGENT_RUN_ID" ]]; then echo "$AGENT_RUN_ID"; else echo "NULL"; fi), $(if [[ -n "$AGENT_TYPE" ]]; then echo "'$AGENT_TYPE'"; else echo "NULL"; fi), $(if [[ -n "$SPECIALIST" ]]; then echo "'$SPECIALIST'"; else echo "NULL"; fi), $(if [[ -n "$PERSONA" ]]; then echo "'$PERSONA'"; else echo "NULL"; fi), '${MESSAGE//\'/\'\'}') RETURNING id" | awk '{print "{\"id\": "$1"}"}'
```

- [ ] **Step 7:** Create `scripts/db/db-query.sh`:

```bash
#!/bin/bash
# db-query.sh — Run arbitrary SQL against the dev-team database
# Usage: db-query.sh "<sql>"              — JSON output
#        db-query.sh --table "<sql>"      — formatted table output
# Output: JSON array or ASCII table to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

FORMAT="json"
SQL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --table) FORMAT="table"; shift ;;
    *) SQL="$1"; shift ;;
  esac
done

if [[ -z "$SQL" ]]; then
  echo "Usage: db-query.sh [--table] \"<sql>\"" >&2
  exit 1
fi

if [[ "$FORMAT" == "table" ]]; then
  sqlite3 -header -column "$DB_PATH" "$SQL"
else
  sqlite3 -json "$DB_PATH" "$SQL"
fi
```

- [ ] **Step 8:** Create `scripts/db/db-cleanup.sh`:

```bash
#!/bin/bash
# db-cleanup.sh — Age out old workflow runs and cascading data
# Usage: db-cleanup.sh --older-than <duration>  (e.g., 90d, 6m, 1y)
# Does NOT delete projects — only their run history
# Output: Summary of deleted records to stdout

set -euo pipefail

DB_PATH="${HOME}/.agentic-cookbook/dev-team/dev-team.db"
"$(dirname "$0")/db-init.sh" > /dev/null

DURATION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --older-than) DURATION="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$DURATION" ]]; then
  echo "Usage: db-cleanup.sh --older-than <duration> (e.g., 90d, 6m, 1y)" >&2
  exit 1
fi

# Parse duration to SQLite date modifier
case "$DURATION" in
  *d) DAYS="${DURATION%d}"; MODIFIER="-$DAYS days" ;;
  *m) MONTHS="${DURATION%m}"; MODIFIER="-$MONTHS months" ;;
  *y) YEARS="${DURATION%y}"; MODIFIER="-$YEARS years" ;;
  *) echo "Invalid duration format. Use Nd, Nm, or Ny (e.g., 90d, 6m, 1y)" >&2; exit 1 ;;
esac

CUTOFF_DATE=$(date -v"${MODIFIER// /}" +%Y-%m-%d 2>/dev/null || date -d "$MODIFIER" +%Y-%m-%d 2>/dev/null)

echo "Cleaning up runs older than $CUTOFF_DATE..." >&2

# Get run IDs to delete
RUN_IDS=$(sqlite3 "$DB_PATH" "SELECT id FROM workflow_runs WHERE completed < '$CUTOFF_DATE'")

if [[ -z "$RUN_IDS" ]]; then
  echo "{\"deleted_runs\": 0}"
  exit 0
fi

# Delete cascading (messages, artifacts, findings via agent_runs, agent_runs, then runs)
DELETED_MESSAGES=$(sqlite3 "$DB_PATH" "DELETE FROM messages WHERE workflow_run_id IN (SELECT id FROM workflow_runs WHERE completed < '$CUTOFF_DATE'); SELECT changes()")
DELETED_ARTIFACTS=$(sqlite3 "$DB_PATH" "DELETE FROM artifacts WHERE workflow_run_id IN (SELECT id FROM workflow_runs WHERE completed < '$CUTOFF_DATE'); SELECT changes()")
DELETED_FINDINGS=$(sqlite3 "$DB_PATH" "DELETE FROM findings WHERE agent_run_id IN (SELECT id FROM agent_runs WHERE workflow_run_id IN (SELECT id FROM workflow_runs WHERE completed < '$CUTOFF_DATE')); SELECT changes()")
DELETED_AGENTS=$(sqlite3 "$DB_PATH" "DELETE FROM agent_runs WHERE workflow_run_id IN (SELECT id FROM workflow_runs WHERE completed < '$CUTOFF_DATE'); SELECT changes()")
DELETED_RUNS=$(sqlite3 "$DB_PATH" "DELETE FROM workflow_runs WHERE completed < '$CUTOFF_DATE'; SELECT changes()")

echo "{\"deleted_runs\": $DELETED_RUNS, \"deleted_agents\": $DELETED_AGENTS, \"deleted_findings\": $DELETED_FINDINGS, \"deleted_artifacts\": $DELETED_ARTIFACTS, \"deleted_messages\": $DELETED_MESSAGES}"
```

- [ ] **Step 9:** Make all scripts executable and commit:

```bash
chmod +x scripts/db/db-project.sh scripts/db/db-run.sh scripts/db/db-agent.sh scripts/db/db-finding.sh scripts/db/db-artifact.sh scripts/db/db-message.sh scripts/db/db-query.sh scripts/db/db-cleanup.sh
git add scripts/db/
git commit -m "Add all DB shell scripts (project, run, agent, finding, artifact, message, query, cleanup)"
git push
```

---

## Task 3: Integrate DB into workflows

This is the judgment task — weaving DB calls into each workflow without disrupting the existing flow.

**Files:**
- Modify: `skills/dev-team/SKILL.md` (router — add db-init to startup)
- Modify: `skills/dev-team/workflows/interview.md`
- Modify: `skills/dev-team/workflows/create-project-from-code.md`
- Modify: `skills/dev-team/workflows/generate.md`
- Modify: `skills/dev-team/workflows/create-code-from-project.md`
- Modify: `skills/dev-team/workflows/lint.md`
- Modify: `skills/dev-team/workflows/compare-code.md`
- Modify: `skills/dev-team/workflows/view-project.md`

- [ ] **Step 1:** Read all workflow files and the router to understand current structure

- [ ] **Step 2:** Update router `skills/dev-team/SKILL.md`:
  - In the Configuration section, after config loading, add: `Run: ${CLAUDE_PLUGIN_ROOT}/scripts/db/db-init.sh`
  - This ensures the DB exists before any workflow runs
  - Bump version to 0.5.0

- [ ] **Step 3:** Add a standard "DB Integration" section to each workflow. This section goes after the Overview and before Phase 1 in each workflow:

```markdown
## DB Integration

At workflow start:
```
PROJECT_ID=$(${CLAUDE_PLUGIN_ROOT}/scripts/db/db-project.sh --name <project-name> --path <project-path>)
RUN_ID=$(${CLAUDE_PLUGIN_ROOT}/scripts/db/db-run.sh start --project $PROJECT_ID --workflow <workflow-name>)
```

Pass `$PROJECT_ID` and `$RUN_ID` to all spawned agents.

Before each agent spawn, log: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-agent.sh start --run $RUN_ID --agent <agent-type> [--specialist <domain>]`

After each agent completes: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-agent.sh complete --id $AGENT_ID --status completed`

After writing any file to disk, also log to DB: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-artifact.sh write --project $PROJECT_ID --run $RUN_ID --path <file-path> --category <category>`

Log significant activity: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-message.sh --run $RUN_ID --message "<description of what's happening>"`

At workflow end: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-run.sh complete --id $RUN_ID --status completed`

On error: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-run.sh complete --id $RUN_ID --status failed`
```

- [ ] **Step 4:** Add workflow-specific DB usage:

**interview.md** — After each transcript write, log artifact. After each analysis, log artifact. Log messages from specialists.

**create-project-from-code.md** — Add resumability check at start:
```
Check for interrupted run: db-run.sh --latest --project $PROJECT_ID --workflow create-project-from-code
If status='interrupted': query agent_runs to determine last completed phase, skip to next.
```
Log each recipe as artifact. Log architecture map and scope report as artifacts.

**generate.md** — Read previous lint findings at start:
```
Previous findings: db-finding.sh --list --project $PROJECT_ID --type FAIL --status open
Skip re-reviewing issues already flagged by lint.
```
Log each review as artifact. Log findings (suggestions accepted/rejected).

**create-code-from-project.md** — Add resumability (same pattern as create-project-from-code). Log each specialist pass as agent run. Log generated code as artifacts. Log build results.

**lint.md** — Log findings (PASS/WARN/FAIL). Add trend query:
```
Previous run: db-query.sh "SELECT type, COUNT(*) FROM findings WHERE project_id=$PROJECT_ID GROUP BY type"
Show: "Previous run: N FAILs, M WARNs. This run: ..."
```

**compare-code.md** — Log comparison record. Log requirements coverage. Add trend:
```
db-query.sh "SELECT preservation_pct, created FROM comparisons WHERE project_id=$PROJECT_ID ORDER BY created"
Show: "Preservation trend: 87% → 93% → current"
```

**view-project.md** — Read from DB to enrich the HTML view:
```
Query recent findings, workflow history, comparison trends to display in the viewer.
```

- [ ] **Step 5:** Commit and push

```bash
git add skills/dev-team/
git commit -m "Integrate shared database into all workflows

Router calls db-init at startup. Each workflow logs project, run, agents,
artifacts, findings, and messages. Adds resumability to create-project-from-code
and create-code-from-project. Adds trend tracking to lint and compare-code.
Router bumped to v0.5.0."
git push
```

---

## Task 4: Update CLAUDE.md and documentation

**Files:**
- Modify: `.claude/CLAUDE.md`

- [ ] **Step 1:** Read `.claude/CLAUDE.md`

- [ ] **Step 2:** Add a Database section after the Config section:

```markdown
## Database

Shared state: `~/.agentic-cookbook/dev-team/dev-team.db` (SQLite)

Tracks workflow runs, agent runs, findings, artifacts (full content), specialist assignments, comparisons, and agent activity messages. Accessed via shell scripts in `scripts/db/`.

Key scripts: `db-init.sh` (create/migrate), `db-project.sh`, `db-run.sh`, `db-agent.sh`, `db-finding.sh`, `db-artifact.sh`, `db-message.sh`, `db-query.sh` (ad-hoc SQL), `db-cleanup.sh` (age out old runs).
```

- [ ] **Step 3:** Update Repository Structure to include `scripts/db/`

- [ ] **Step 4:** Commit and push

```bash
git add .claude/CLAUDE.md
git commit -m "Document shared database in CLAUDE.md"
git push
```

---

## Verification

1. **DB init works:**
   ```bash
   scripts/db/db-init.sh
   # Should output: /Users/<user>/.agentic-cookbook/dev-team/dev-team.db
   sqlite3 ~/.agentic-cookbook/dev-team/dev-team.db ".tables"
   # Should list all 10 tables + meta
   ```

2. **Project CRUD:**
   ```bash
   scripts/db/db-project.sh --name test-project --path /tmp/test
   # {"id": 1}
   scripts/db/db-project.sh --list
   # JSON array with test-project
   ```

3. **Workflow run lifecycle:**
   ```bash
   scripts/db/db-run.sh start --project 1 --workflow lint
   # {"id": 1}
   scripts/db/db-run.sh complete --id 1 --status completed
   # {"id": 1, "status": "completed"}
   ```

4. **Agent run lifecycle:**
   ```bash
   scripts/db/db-agent.sh start --run 1 --agent artifact-reviewer --specialist security
   # {"id": 1}
   scripts/db/db-agent.sh complete --id 1 --status completed
   ```

5. **Finding recording:**
   ```bash
   scripts/db/db-finding.sh --project 1 --type FAIL --severity critical --description "Missing auth check"
   # {"id": 1}
   scripts/db/db-finding.sh --list --project 1
   # JSON array with the finding
   ```

6. **Ad-hoc query:**
   ```bash
   scripts/db/db-query.sh "SELECT * FROM projects"
   scripts/db/db-query.sh --table "SELECT * FROM workflow_runs"
   ```

7. **Cleanup:**
   ```bash
   scripts/db/db-cleanup.sh --older-than 0d
   # Should delete the test data
   ```

8. **Router initializes DB:**
   ```
   /dev-team help
   # Should work without errors (db-init runs silently)
   ```
