---
name: dev-team
version: 0.2.1
description: Multi-agent dev team for product discovery, project creation, specialist review, building, and linting. Subcommands: interview, create-project-from-code, generate, create-code-from-project, lint, view-project.
allowed-tools: Read, Glob, Grep, Agent, Write, Edit, AskUserQuestion, Bash(git *), Bash(mkdir *), Bash(ls *), Bash(date *), Bash(cat *), Bash(wc *), Bash(uuidgen), Bash(chmod *), Bash(open *), WebFetch
argument-hint: <command> [args...] — commands: interview, create-project-from-code, generate, create-code-from-project, lint, view-project
---

# Dev Team v0.2.1

## Startup

**First action**: If `$ARGUMENTS` is `--version`, print `dev-team v0.2.1` and stop.

Otherwise, print `dev-team v0.2.1` as the first line of output.

**Version check**: Run `${CLAUDE_PLUGIN_ROOT}/scripts/version-check.sh "${CLAUDE_SKILL_DIR}" "0.2.1"`. If it outputs a warning, print it and continue.

## Configuration

**Config path**: If `$ARGUMENTS` contains `--config <path>`, extract it.

Run: `${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh` with `--config <path>` if specified. If the script fails (exit code 1), the error message tells the user what's wrong.

Extract `cookbook_repo`, `workspace_repo`, and `user_name` from the JSON output.

If config doesn't exist and the subcommand is NOT `interview`: "I need a config file. Run `/dev-team interview` first to set one up, or create `~/.agentic-cookbook/dev-team/config.json` with `workspace_repo`, `cookbook_repo`, and `user_name` fields."

## Routing

Parse the first positional argument from `$ARGUMENTS` as the subcommand. Everything after it becomes the subcommand's arguments.

| Subcommand | Workflow File |
|------------|--------------|
| `interview` | `${CLAUDE_SKILL_DIR}/workflows/interview.md` |
| `create-project-from-code` | `${CLAUDE_SKILL_DIR}/workflows/create-project-from-code.md` |
| `generate` | `${CLAUDE_SKILL_DIR}/workflows/generate.md` |
| `create-code-from-project` | `${CLAUDE_SKILL_DIR}/workflows/create-code-from-project.md` |
| `lint` | `${CLAUDE_SKILL_DIR}/workflows/lint.md` |
| `view-project` | `${CLAUDE_SKILL_DIR}/workflows/view-project.md` |

Read the workflow file and follow its instructions. Pass the remaining arguments and the loaded config as the workflow's input.

If no subcommand is provided or the subcommand is `help`, print:

```
Dev Team v0.2.1 — Multi-agent product development

Commands:
  interview                    Product discovery interview
  create-project-from-code     Reverse-engineer codebase into cookbook project
  generate                     Specialist review of cookbook project recipes
  create-code-from-project      Build working code from cookbook project
  lint                         Evaluate artifacts against cookbook standards
  view-project                 View cookbook project in browser

Usage: /dev-team <command> [args...]
```

If the subcommand is unrecognized, print the help text above and say "Unknown command: `<subcommand>`".
