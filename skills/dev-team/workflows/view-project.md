<!-- Workflow: view-project — loaded by /dev-team router -->

# View Project

## Overview

You are the **Project Viewer** — you generate a self-contained HTML dashboard from a cookbook project and open it in the browser. No agents, no subprocesses — just read, assemble, and display.

Your job:
1. Load and validate `cookbook-project.json`
2. Read all recipe markdown files and context files referenced in the manifest
3. Inject the data into the HTML viewer template
4. Write the result to a temp file and open it in the default browser

## DB Integration

This workflow is read-only — it does not log runs to the DB. Query the DB to enrich the HTML view:

- Recent workflow runs: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-query.sh "SELECT workflow, status, started, completed FROM workflow_runs WHERE project_id=$PROJECT_ID ORDER BY started DESC LIMIT 10"`
- Open findings: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-finding.sh --list --project $PROJECT_ID --status open`
- Comparison trends: `${CLAUDE_PLUGIN_ROOT}/scripts/db/db-query.sh "SELECT preservation_pct, created FROM comparisons WHERE project_id=$PROJECT_ID ORDER BY created"`

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

### Read Context Files
For each entry in the manifest's `context` object:
1. Read the file at `<project-dir>/<path>`
2. Store the content keyed by the context entry name (e.g., "architecture-map", "scope-report")

If a context file is missing, skip it silently.

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
  "context": {
    "architecture-map": "markdown content...",
    "scope-report": "markdown content..."
  }
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
