---
name: dev-team-view-project
version: 0.1.0
description: Generate a human-readable HTML view of a cookbook project and open it in the browser — shows component tree, recipe details, dependencies, and context files
allowed-tools: Read, Glob, Grep, Write, Bash(open *), Bash(mktemp *), Bash(date *), Bash(cat *), Bash(ls *), AskUserQuestion
argument-hint: <project-path> [--config <path>]
---

# View Project v0.1.0

## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `view-project v0.1.0` and stop.

Otherwise, print `view-project v0.1.0` as the first line of output, then proceed.

**Version check**: Run `${CLAUDE_PLUGIN_ROOT}/scripts/version-check.sh "${CLAUDE_SKILL_DIR}" "0.1.0"`. If it outputs a warning, print it and continue.

## Overview

You are the **Project Viewer** — you generate a self-contained HTML dashboard from a cookbook project and open it in the browser. No agents, no subprocesses — just read, assemble, and display.

Your job:
1. Load and validate `cookbook-project.json`
2. Read all recipe markdown files and context files referenced in the manifest
3. Inject the data into the HTML viewer template
4. Write the result to a temp file and open it in the default browser

## Configuration

**Config path**: If `$ARGUMENTS` contains `--config <path>`, use that path.

Run: `${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh` with `--config <path>` if specified. If the script fails (exit code 1), the error message tells the user what's wrong.

Extract `cookbook_repo`, `workspace_repo`, and `user_name` from the JSON output.

If config doesn't exist: "I need a config file. Create `~/.agentic-cookbook/dev-team/config.json` with `workspace_repo`, `cookbook_repo`, and `user_name` fields."

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
