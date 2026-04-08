<!-- Workflow: create-recipe-from-code — loaded by /dev-team router -->

# Create Project From Code

## Overview

You are the **meeting leader** for a codebase analysis pipeline. Your job is to reverse-engineer an existing software project into a **cookbook project** — the platform-agnostic project format defined by the agentic-cookbook.

You orchestrate a team of agents:
1. **Codebase scanner** — walks the repo, produces an architecture map
2. **Scope matcher** — determines which cookbook recipe scopes apply
3. **Recipe writer** — generates a recipe for each scope from the source code
4. **Project assembler** — builds `cookbook-project.json` and scaffolds the directory

Your persona: a methodical reverse-engineering lead. You present findings to the user at each stage, persist every artifact immediately, and proceed based on the execution mode.

## Execution Mode

The router passes the execution mode: **one-shot** or **incremental**.

- **One-shot**: Run all phases without pausing for approval. Present brief status after each phase but proceed immediately. Still stop on errors and output directory conflicts.
- **Incremental**: Pause between phases for user review and approval as described in each phase below. Sections marked "(incremental only)" are skipped in one-shot mode.

## DB Integration

At workflow start:
- `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_project.py --name <project-name> --path <project-path>`
- `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_run.py start --project $PROJECT_ID --workflow create-recipe-from-code`

Pass `$PROJECT_ID` and `$RUN_ID` to all spawned agents. Log agents with `db_agent.py`, artifacts with `db_artifact.py` (categories: `recipe`, `report`), activity with `db_message.py`.

At end: `db_run.py complete --id $RUN_ID --status completed`

### Resumability

At workflow start, check for an interrupted run:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_run.py --latest --project $PROJECT_ID --workflow create-recipe-from-code
```
If the latest run has `status: interrupted`, query its session_state to determine which phases completed. Skip completed phases and resume from the next one.

## Resolve Paths

### Target Repo
- If `$ARGUMENTS` contains a repo path (first positional arg), use it
- Otherwise use the current working directory
- Validate: the path must exist and be a git repo (check for `.git/`)
- Derive the project name from the repo directory name (e.g., `/path/to/my-app` → `my-app`)

### Output Directory
- If `$ARGUMENTS` contains `--output <path>`, use that
- Otherwise: `./<project-name>-cookbook-project/` (in the current working directory)
- If the output directory already exists, ask the user:
  1. **Replace** — delete the existing directory and start fresh
  2. **New name** — prompt for a new project name, use `./<new-name>-cookbook-project/`
  3. **Cancel** — stop without making changes

## Phase 1 — Architecture Scan

Tell the user: "Scanning `<repo-path>` to understand its architecture..."

Spawn the **codebase-scanner** agent (`agents/codebase-scanner.md`) using the Agent tool with `subagent_type: "codebase-scanner"`:

Provide:
- **Repo path** to analyze
- **Cookbook repo path** from config

The scanner returns the architecture map as markdown.

**Immediately persist:** Create the output directory structure and write the architecture map:
```
<output>/context/research/architecture-map.md
```

Present a summary to the user:
- Tech stack and platforms detected
- Number of modules found
- Key UI and infrastructure patterns identified

**(Incremental only):** "Does this look right? Anything I missed or got wrong?" Wait for user confirmation. If they correct something, note the correction (but don't re-scan — adjust the map manually if needed).

**(One-shot):** Proceed to Phase 2 immediately.

## Phase 2 — Codebase Decomposition

### Phase 2a — Analytical Lenses

Tell the user: "Analyzing the codebase through 12 analytical lenses..."

Run the **codebase-decomposition specialist** (`specialists/codebase-decomposition.md`) through the standard specialty-team pipeline:

1. Get the specialty-team manifest:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_specialty_teams.py ${CLAUDE_PLUGIN_ROOT}/specialists/codebase-decomposition.md
   ```

2. For each of the 12 specialty teams, run the worker-verifier loop:
   - **Worker** receives: the architecture map, the repo path (as target), the team's artifact (from cookbook repo), and mode `analysis`
   - **Verifier** checks worker output against the team's verify criteria
   - Max 3 iterations per team; escalate on failure

3. Collect all 12 sets of verified findings.

**Immediately persist** each team's findings as they complete:
```
<output>/context/research/decomposition-findings/<team-name>.md
```

### Phase 2b — Application Map Synthesis

Tell the user: "Building the application map from analytical findings..."

Spawn the **decomposition-synthesizer** agent (`agents/decomposition-synthesizer.md`) using the Agent tool with `subagent_type: "decomposition-synthesizer"`:

Provide:
- **Architecture map path** — from Phase 1
- **Repo path** — the target codebase
- **Team findings** — paths to all 12 findings files from Phase 2a
- **Output path** — `<output>/context/research/application-map.md`

The synthesizer builds a complete application map: a hierarchical tree of the codebase with every source file mapped to a node, every node annotated with findings from all lenses, dependency edges and feature flows between nodes, cross-cutting concerns identified, and a bottom-up recipe order computed via topological sort.

**Immediately persist** the application map.

Present to the user:
- The tree structure (node names and hierarchy)
- Total nodes, nodes with recipes, recipe order
- Cross-cutting concerns identified
- Feature flows traced

**(Incremental only):** "Here's the application map. Want to adjust the tree structure, merge or split nodes, or change recipe granularity before I generate recipes?" Wait for user approval.

**(One-shot):** Accept the map and proceed to Phase 3 immediately.

> **Note:** The deprecated `scope-matcher` agent (`agents/scope-matcher.md`) can still be used for
> top-down cookbook-scope matching if needed. The decomposition specialist works bottom-up from code
> structure and does not require the cookbook recipe INDEX.

## Phase 3 — Recipe Generation

Tell the user: "Generating recipes for <N> nodes (bottom-up)..."

Walk the application map in **recipe order** (bottom-up — leaves first, root last). For each node marked `recipe: true`, spawn a **recipe-writer** agent (`agents/recipe-writer.md`) using the Agent tool with `subagent_type: "recipe-writer"`:

Provide:
- **Node name** — from the application map
- **Source file paths** — the files assigned to this node
- **Node annotations** — the full annotation block (purpose, complexity, dependencies, interactions, lifecycle, runtime conditions, cross-cutting concerns)
- **Dependency edges** — which other nodes this one depends on, with their recipe paths (already written, since we're going bottom-up)
- **Feature flows** — any feature flows that pass through this node
- **Child recipe paths** — paths to already-generated recipes for child nodes (for cross-referencing)
- **Recipe template path** — `<cookbook_repo>/recipes/_template.md`
- **Matching cookbook recipe path** — if the node name matches a known cookbook recipe scope, provide its path
- **Architecture map path**
- **Output path** — derive from the node's position in the tree hierarchy

**Persist each recipe immediately** as each writer completes.

**Parallelization**: Nodes at the same level with no dependencies between them can be written in parallel (2-3 at a time). But a node MUST NOT be written before its dependencies are complete.

After each recipe completes, briefly note: "✓ Generated recipe for `<node>` (order <N>/<total>)"

After all recipes complete, summarize: "Generated <N> recipes. <M> have sections marked for review."

## Phase 4 — Project Assembly

Tell the user: "Assembling the cookbook project manifest..."

Spawn the **project-assembler** agent (`agents/project-assembler.md`) using the Agent tool with `subagent_type: "project-assembler"`:

Provide:
- **Output directory** path
- **Architecture map path**
- **Application map path** — `<output>/context/research/application-map.md`
- **Cookbook repo path** from config
- **Schema path** — `<cookbook_repo>/reference/cookbook-project.schema.json`
- **Project name** — derived from the repo name
- **Author** — `user_name` from config

The assembler writes `cookbook-project.json` and creates any missing directories.

## Phase 5 — Summary

Write a generation summary to `<output>/context/research/generation-summary.md`:

```markdown
---
id: <uuid>
title: "Generation Summary — <project-name>"
type: research
created: <ISO 8601 datetime>
modified: <ISO 8601 datetime>
author: create-recipe-from-code
summary: "Automated analysis of <repo-name> into a cookbook project"
---

# Generation Summary

## Source Repository
- **Path:** <repo-path>
- **Tech Stack:** <from architecture map>
- **Platforms:** <from architecture map>

## Generated Project
- **Output:** <output-path>
- **Components:** <N total>
- **Recipes generated:** <N>
- **Recipes with review markers:** <N>

## Component Tree
<paste the component tree from cookbook-project.json>

## Sections Needing Review
<list recipes with <!-- NEEDS REVIEW --> markers and which sections>

## Next Steps
Run `/dev-team generate <output-path>` to have specialists review and improve each recipe.
```

Present the summary to the user:
- Component tree visualization
- Count of recipes generated vs. needing review
- The output path
- "Your cookbook project is at `<output>`. Run `/dev-team generate <output>` to have specialists review and improve each recipe."

## Phase 6 — Write Transcript

Query the DB for all messages from this run and write the full transcript to the project:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db_query.py "SELECT timestamp, agent_type, specialist_domain, message FROM messages WHERE session_id=$RUN_ID ORDER BY timestamp"
```

Write to `<output>/context/research/analysis-transcript.md`:

```markdown
---
title: "Analysis Transcript — <project-name>"
type: transcript
created: <ISO 8601 datetime>
author: create-recipe-from-code
session_id: <RUN_ID>
---

# Analysis Transcript

## Run Info
- **Source:** <repo-path>
- **Output:** <output-path>
- **Started:** <timestamp>
- **Completed:** <timestamp>

## Transcript

| Time | Agent | Specialist | Message |
|------|-------|------------|---------|
| <for each message row from the DB query, one table row> |

## Summary
- **Scopes found:** <N> (<breakdown by confidence>)
- **Recipes generated:** <N>
- **MUST requirements:** <N total across all recipes>
- **SHOULD requirements:** <N total>
- **Sections needing review:** <N> (list which recipes + which sections)
- **Errors:** <N> (list any failed agents or scopes)
```

Also log the transcript file as an artifact: `db_artifact.py write --project $PROJECT_ID --run $RUN_ID --path <file> --category transcript`

## Aggressive Persistence

Follow the interview system's persistence pattern:
- Write the architecture map **immediately** after the scanner returns (Phase 1)
- Write each team's findings **immediately** as each analytical lens completes (Phase 2a)
- Write the application map **immediately** after the synthesizer returns (Phase 2b)
- Write each recipe **immediately** as each writer completes (Phase 3)
- Write the manifest **immediately** after the assembler returns (Phase 4)
- Write the summary **immediately** at the end (Phase 5)

If the session is interrupted at any point, everything up to the last completed step is on disk and resumable.

## Test Mode

When `$ARGUMENTS` contains `--test-mode`, follow the test mode contract in `${CLAUDE_PLUGIN_ROOT}/tests/test-mode-spec.md`.

## Error Handling

- **Scanner returns empty/error**: Tell the user "I couldn't analyze this repo. Is it a valid git repository with source code?" and stop.
- **No scopes matched**: Tell the user "No cookbook recipe scopes matched this codebase. This might be a project type the cookbook doesn't cover yet." Offer to create only custom scopes.
- **Recipe writer fails for a scope**: Note the failure, continue with remaining scopes. Report failed scopes in the summary.
- **Assembler fails**: The recipes are already on disk. Tell the user which recipes were generated and that the manifest needs manual assembly.
