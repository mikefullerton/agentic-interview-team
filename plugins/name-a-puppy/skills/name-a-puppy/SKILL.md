---
name: name-a-puppy
version: 0.1.0
description: Interview-driven puppy naming with specialist expertise. A test team for the team-pipeline.
allowed-tools: Read, Glob, Grep, Agent, Write, Edit, AskUserQuestion, Bash(python3 *)
argument-hint: [interview]
---

# Name a Puppy v0.1.0

## Startup

**First action**: Print `name-a-puppy v0.1.0` as the first line of output.

Set `TEAM_PIPELINE_ROOT` to the team-pipeline plugin directory (sibling of this plugin under `plugins/`).

## Routing

Parse the first positional argument from `$ARGUMENTS` as the subcommand.

| Subcommand | Workflow File |
|------------|--------------|
| `interview` | `${CLAUDE_SKILL_DIR}/workflows/interview.md` |

Read the workflow file and follow its instructions.

If no subcommand is provided, default to `interview`.
