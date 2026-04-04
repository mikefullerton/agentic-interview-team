<!-- Workflow: view-project — loaded by /dev-team router -->

# View Project

## Overview

You are the **Project Viewer** — you generate a self-contained HTML dashboard from a cookbook project and open it in the browser. No agents, no subprocesses — just read, assemble, and display.

The viewer is a comprehensive project dashboard showing: component tree, recipe details, architecture sections, scope analysis, specialist contributions with summaries, build logs, reviews, transcript history, and project decisions — all searchable and filterable.

Your job:
1. Load and validate `cookbook-project.json`
2. Read all recipe files, context files, reviews, build logs, and decisions
3. Parse scope-report and architecture-map into discrete sections
4. Query the DB for transcript messages, specialist assignments, and findings
5. Build specialist summaries from review + build log data
6. Inject everything into the HTML viewer template
7. Write the result to a temp file and open it in the default browser

## DB Integration

This workflow is read-only — it does not log runs to the DB. Query the DB to enrich the HTML view:

- Recent sessions: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_query.py "SELECT workflow, status, started, completed FROM sessions WHERE project_id=$PROJECT_ID ORDER BY started DESC LIMIT 20"`
- Open findings: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_finding.py --list --project $PROJECT_ID --status open`
- Specialist assignments: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_query.py "SELECT recipe_path, specialist, tier, approved FROM specialist_assignments WHERE project_id=$PROJECT_ID"`
- Transcript messages: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_query.py "SELECT m.timestamp, m.agent_type, m.specialist_domain, m.persona, m.message FROM messages m JOIN sessions s ON m.session_id=s.id WHERE s.project_id=$PROJECT_ID ORDER BY m.timestamp"`
- Transcript artifacts: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_artifact.py search --project $PROJECT_ID --category transcript`
- Comparison trends: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_query.py "SELECT preservation_pct, created FROM comparisons WHERE project_id=$PROJECT_ID ORDER BY created"`

Include this data in the HTML output if available. If the DB doesn't exist or has no data for this project, skip enrichment gracefully.

## Phase 1 — Load Project

### Resolve Project Path
- If `$ARGUMENTS` contains a project path (first positional arg), use it
- Otherwise check the cwd for `cookbook-project.json`
- If neither: ask "Where is your cookbook project? Provide the path to the directory containing `cookbook-project.json`."

### Validate
- Read `cookbook-project.json`
- Check `"type": "cookbook-project"` is present
- If missing or invalid: "This doesn't look like a cookbook project. Expected a `cookbook-project.json` with `\"type\": \"cookbook-project\"`."

### Parse the Manifest
Extract from the JSON:
- **Project metadata**: `name`, `version`, `description`, `author`, `created`, `modified`, `platforms`
- **Component tree**: Walk the `components` object recursively. For each component:
  - `key` — the component's key name
  - `description` — from the component entry
  - `recipe` — the relative recipe file path (if present)
  - `depends-on` — array of dot-path dependency references
  - `children` — nested components (recursive)
- **Context files**: From the `context` object, collect paths to research files (architecture-map, scope-report, etc.)

Print: "Loaded **<name>** — <N> recipes, <platforms>."

## Phase 2 — Read Content

### Read Recipe Files
For each component that has a `recipe` field:
1. Read the file at `<project-dir>/<recipe-path>`
2. Parse YAML frontmatter to extract: `title`, `summary`, `tags`, `platforms`, `depends-on`, `related`
3. Extract the markdown body (everything after the closing `---`)
4. Store the frontmatter and body on the component's data object

If a recipe file is missing, log a warning and continue — set the recipe body to "(Recipe file not found)".

### Read and Parse Context Files

#### Architecture Map
Read `context/research/architecture-map.md`. Split into sections by `## ` headings. Each section becomes a separate entry:
```json
{ "category": "architecture", "title": "<heading text>", "content": "<section body>" }
```

#### Scope Report
Read `context/research/scope-report.md`. Split into sections by `## ` headings. Each section becomes a separate entry:
```json
{ "category": "scope", "title": "<heading text>", "content": "<section body>" }
```

#### Other Research Files
For any other files in `context/research/` (review-summary.md, build-summary.md, test-report.md), add each as:
```json
{ "category": "research", "title": "<filename without .md, title-cased>", "content": "<full content>" }
```

### Read Reviews
Glob `context/reviews/*.md`. For each file:
1. Read the file
2. Parse the filename to extract recipe slug and specialist domain (format: `<slug>-<specialist>.md` or `<slug>-code-review.md`)
3. Add as:
```json
{ "category": "review", "title": "<specialist display name> — <recipe name>", "content": "<body>", "specialist": "<domain>", "recipe": "<slug>" }
```

### Read Build Logs
Glob `context/build-log/*.md`. For each file:
1. Read the file
2. Parse the filename to extract type (scaffold-report, build-report, or `<slug>-generation`)
3. For generation logs, parse specialist augmentation sections (look for `### <Specialist Name>` subsections under each recipe's generation log)
4. Add as:
```json
{ "category": "build", "title": "<descriptive title>", "content": "<body>", "specialist": "<domain if applicable>", "recipe": "<slug if applicable>" }
```

### Read Decisions
Glob `context/decisions/*.md`. For each file:
```json
{ "category": "decision", "title": "<title from frontmatter or filename>", "content": "<body>" }
```

### Build Specialist Summaries
Aggregate data from reviews and build logs to build per-specialist summaries:

For each specialist that appears in reviews or build logs:
1. Collect all recipes they reviewed (from review files)
2. Collect all code changes they made (from generation log specialist sections)
3. Collect findings from DB if available
4. Collect assignments from DB if available
5. Build a summary object:
```json
{
  "domain": "security",
  "displayName": "Security",
  "recipes": ["app.main-window", "app.settings"],
  "summary": "<2-3 sentence summary of what this specialist contributed>",
  "changes": [
    { "recipe": "main-window", "description": "Added input validation, CSP headers, and auth token encryption" },
    { "recipe": "settings", "description": "Added credential encryption for stored passwords" }
  ],
  "reviewFindings": 3,
  "suggestionsApproved": 2
}
```

Write the summary prose yourself by reading the specialist's review findings and code changes, then composing a concise description of their contributions. Focus on what cookbook principles were applied and where.

### Query DB for Transcript
If the database exists and has data for this project:
1. Query messages table for all messages ordered by timestamp
2. Query artifacts table for transcript category
3. For transcript artifacts, read the full content
4. Build transcript array:
```json
[
  {
    "timestamp": "2026-04-02T10:30:00Z",
    "agent": "specialist-interviewer",
    "specialist": "security",
    "persona": "Security Specialist",
    "message": "What authentication method will the app use?"
  }
]
```

### Query DB for Timeline
Query sessions for this project to build a timeline:
```json
[
  { "workflow": "interview", "status": "completed", "started": "...", "completed": "..." },
  { "workflow": "create-project-from-code", "status": "completed", "started": "...", "completed": "..." }
]
```

## Phase 3 — Generate HTML

### Build PROJECT_DATA
Assemble a JSON object with this structure:

```json
{
  "project": {
    "name": "...",
    "version": "...",
    "description": "...",
    "author": "...",
    "created": "...",
    "modified": "...",
    "platforms": ["..."]
  },
  "components": [
    {
      "key": "app",
      "description": "...",
      "recipePath": "app/component/component.md",
      "dependsOn": ["app.other"],
      "recipe": {
        "title": "...",
        "summary": "...",
        "tags": ["..."],
        "platforms": ["..."],
        "body": "markdown content..."
      },
      "children": [ ... ]
    }
  ],
  "sections": [
    { "category": "architecture", "title": "Tech Stack", "content": "..." },
    { "category": "architecture", "title": "Module Structure", "content": "..." },
    { "category": "scope", "title": "Matched Scopes", "content": "..." },
    { "category": "scope", "title": "Custom Scopes", "content": "..." },
    { "category": "research", "title": "Build Summary", "content": "..." },
    { "category": "review", "title": "Security — Main Window", "content": "...", "specialist": "security", "recipe": "main-window" },
    { "category": "build", "title": "Generation Log — Toolbar", "content": "...", "specialist": "...", "recipe": "..." },
    { "category": "decision", "title": "Auth Strategy", "content": "..." }
  ],
  "specialists": [ ... ],
  "transcript": [ ... ],
  "timeline": [ ... ]
}
```

The `components` array mirrors the hierarchical component tree from the manifest. Components without a `recipe` field should still appear (as group nodes) but with `recipe: null`.

### Inject Into Template
1. Read the HTML template at `${CLAUDE_SKILL_DIR}/viewer.html`
2. Replace the `<!-- PROJECT_DATA -->` comment with:
   ```
   <script>const PROJECT_DATA = <json>;</script>
   ```
   where `<json>` is the JSON-serialized PROJECT_DATA object
3. Write the result to `/tmp/cookbook-viewer-<project-name-slug>.html`
   - Slug the project name: lowercase, replace spaces/special chars with hyphens

### Open in Browser
Run: `open /tmp/cookbook-viewer-<slug>.html`

Print: "Opened project viewer in your browser. File saved to `/tmp/cookbook-viewer-<slug>.html`."

## Error Handling

- **No cookbook-project.json**: Ask user for the path.
- **Invalid JSON**: Print the parse error and stop.
- **Missing recipe files**: Warn per file, continue with remaining recipes.
- **Empty project (no recipes)**: Still generate the viewer — it will show the overview with 0 recipes.
- **Template not found**: Print "Viewer template not found at `${CLAUDE_SKILL_DIR}/viewer.html`. The skill installation may be incomplete."
- **No DB or no project in DB**: Skip all DB queries gracefully. Transcript/timeline/specialist assignments will be empty arrays.
- **No reviews/build-logs/decisions**: Corresponding sidebar categories will simply not appear.
