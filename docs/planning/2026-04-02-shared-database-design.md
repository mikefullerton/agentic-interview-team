# Shared Database Design Spec

## Summary

Add a SQLite database as shared state for the dev-team plugin. Located at `~/.agentic-cookbook/dev-team/dev-team.db`. Accessed via shell scripts in `scripts/db/`. Enables cross-workflow resumability, cross-project insights, agent activity logging, and structured querying of all artifacts.

## Database Location

`~/.agentic-cookbook/dev-team/dev-team.db` — system-level, alongside config.json. Single DB across all projects enables cross-project queries and insights.

Config (`config.json`) stays separate — static settings vs dynamic state.

## Schema (10 tables)

```sql
-- Schema version tracking
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

-- Core
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
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

-- Findings & tracking
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

-- Specialist tracking
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

-- Content
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

-- Activity log
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
```

### Enums

- `workflow_runs.workflow`: `interview`, `create-recipe-from-code`, `generate`, `create-code-from-recipe`, `lint`, `compare-code`, `view-recipe`
- `workflow_runs.status`: `running`, `completed`, `failed`, `interrupted`
- `agent_runs.status`: `running`, `completed`, `failed`
- `findings.type`: `requirement`, `regression`, `suggestion`, `FAIL`, `WARN`, `PASS`
- `findings.severity`: `critical`, `important`, `minor`
- `findings.status`: `open`, `accepted`, `rejected`, `fixed`
- `artifacts.category`: `transcript`, `analysis`, `recipe`, `review`, `build-log`, `report`, `comparison`, `summary`
- `requirements.keyword`: `MUST`, `SHOULD`, `MAY`

## Shell Script API

All scripts in `scripts/db/`. Each calls `db-init.sh` internally to ensure schema exists (idempotent). All output JSON to stdout, errors to stderr. Exit 0 on success, 1 on failure.

### db-init.sh
- Creates DB file if missing
- Runs `CREATE TABLE IF NOT EXISTS` for all tables
- Stores schema version in `meta` table
- Runs migrations if schema version is behind current
- Idempotent — safe to call on every workflow startup

### db-project.sh
- `db-project.sh --name <name> --path <path>` — create or get project, returns JSON `{"id": N}`
- `db-project.sh --get <id>` — get project by ID
- `db-project.sh --list` — list all projects
- If project with same name exists, returns existing ID (upsert on name)

### db-run.sh
- `db-run.sh start --project <id> --workflow <name>` — creates run, returns `{"id": N}`
- `db-run.sh complete --id <id> --status <completed|failed|interrupted>` — updates run
- `db-run.sh --get <id>` — get run details
- `db-run.sh --latest --project <id> --workflow <name>` — get most recent run for resume checks

### db-agent.sh
- `db-agent.sh start --run <id> --agent <type> [--specialist <domain>]` — returns `{"id": N}`
- `db-agent.sh complete --id <id> --status <completed|failed> [--output-path <path>]`

### db-finding.sh
- `db-finding.sh --agent-run <id> --project <id> --type <type> --severity <sev> --description "<text>" [--artifact-path <path>]`
- `db-finding.sh update --id <id> --status <accepted|rejected|fixed>`
- `db-finding.sh --list --project <id> [--type <type>] [--status <status>]`

### db-artifact.sh
- `db-artifact.sh write --project <id> [--run <id>] [--agent-run <id>] --path <path> --category <cat> [--specialist <domain>]`
  - Reads the file at `<path>`, parses frontmatter, computes hash, stores full content
  - If artifact with same path exists, bumps version and updates
- `db-artifact.sh get --id <id>` — returns artifact metadata + content
- `db-artifact.sh search --project <id> --category <cat> [--specialist <domain>] [--text <search>]`

### db-message.sh
- `db-message.sh --run <id> [--agent-run <id>] [--agent-type <type>] [--specialist <domain>] [--persona <name>] --message "<text>"`

### db-query.sh
- `db-query.sh "<sql>"` — runs arbitrary SQL, returns JSON array
- `db-query.sh --table "<sql>"` — returns as formatted table (for human display)

### db-cleanup.sh
- `db-cleanup.sh --older-than <duration>` — e.g., `90d`, `6m`, `1y`
- Deletes workflow_runs and cascading data older than the threshold
- Does NOT delete projects (only their run history)

## Workflow Integration

### Startup (router)
After config loading, before routing: `db-init.sh`

### Per-workflow
Start: `db-project.sh` + `db-run.sh start`
End: `db-run.sh complete`
Error: `db-run.sh complete --status failed`

### Per-agent
Agents receive `$RUN_ID` and `$PROJECT_ID`. Call `db-agent.sh start/complete`, `db-message.sh`, `db-finding.sh`, `db-artifact.sh write`.

### Resumability
Check for interrupted runs at workflow start. Query agent_runs to determine what completed. Skip completed phases, resume from interrupted.

### Files
DB stores artifacts AND files continue to be written to disk. DB is the structured index; files are human-readable output. `content_hash` detects drift.

## Cross-Project Insights
Single DB enables: specialist effectiveness, common regressions, round-trip improvement tracking, build success rates.

## Aging
`db-cleanup.sh --older-than 90d` removes old runs. Projects are never deleted.
