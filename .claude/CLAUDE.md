# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Skills

Single entry point: `/dev-team <command>`

| Command | Role | Responsibility |
|---------|------|---------------|
| `interview` | Interviewer | Discover product requirements through structured and exploratory questioning with specialist expertise |
| `create-project-from-code` | Project Creator | Reverse-engineer a codebase into a cookbook project |
| `generate` | Project Generator | Improve a cookbook project through specialist review |
| `create-code-from-project` | Project Builder | Build working code from a cookbook project |
| `lint` | Linter | Evaluate any artifact against cookbook standards |
| `align-specialists` | Alignment Reviewer | Review specialist-cookbook alignment after guideline changes |
| `compare-code` | Comparator | Compare two code projects for round-trip verification |
| `view-project` | Viewer | Generate HTML view of a cookbook project |

## Architecture

Three repos:
- **This repo (plugin)** — agents, skills, specialist research
- **agentic-cookbook** — upstream knowledge (principles, guidelines, compliance)
- **Workspace repo** — per-user data (profiles, transcripts, analyses, project builds)

## Repository Structure

```
.claude-plugin/            # Plugin manifest
agents/                    # 19 subagent definitions
specialists/               # 19 specialist definitions (13 domain + 6 platform)
skills/
  dev-team/                # Single skill with subcommand routing
    SKILL.md               # Router
    workflows/             # One workflow file per subcommand
scripts/                   # Shell scripts for deterministic operations
  db/                      # Database shell script API
services/
  dashboard/               # Live workflow dashboard (Flask, read-only)
docs/
  planning/                # Design specs and plans
  research/                # Specialist mapping and assignment rules
tests/                     # Test harness and personas
```

## Local Testing

Symlinks in `.claude/` point to top-level dirs for local testing. These are gitignored.

To test locally: `cd` into this repo and invoke `/dev-team interview`.

## Database

Shared state: `~/.agentic-cookbook/dev-team/dev-team.db` (SQLite)

Tracks workflow runs, agent runs, findings, artifacts (full content), specialist assignments, comparisons, and agent activity messages. Accessed via shell scripts in `scripts/db/`.

Key scripts: `db-init.sh` (create/migrate), `db-project.sh`, `db-run.sh`, `db-agent.sh`, `db-finding.sh`, `db-artifact.sh`, `db-message.sh`, `db-query.sh` (ad-hoc SQL), `db-cleanup.sh` (age out old runs).

## Config

System config: `~/.agentic-cookbook/dev-team/config.json`

```json
{
  "workspace_repo": "<path to workspace repo>",
  "cookbook_repo": "<path to agentic-cookbook>",
  "user_name": "<user name>",
  "authorized_repos": []
}
```
