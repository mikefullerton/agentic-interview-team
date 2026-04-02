# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Skills

| Role | Command | Responsibility |
|------|---------|---------------|
| **Interviewer** | `/dev-team-interview` | Discover product requirements through structured and exploratory questioning with specialist expertise |
| **Cookbook Analyzer** | `/dev-team-create-project-from-code <target>` | Reverse-engineer an artifact into cookbook format — codebase into cookbook project |
| **Cookbook Project Generator** | `/dev-team-generate <target>` | Improve a cookbook project through specialist review — review recipes, suggest changes, apply approved improvements |
| **Project Builder** | `/dev-team-build <target>` | Build working code from a cookbook project — scaffold, generate, augment with specialists, compile, test |
| **Linter** | `/dev-team-lint <target>` | Evaluate any artifact against cookbook standards — skills, rules, agents, recipes, implementations — produce PASS/WARN/FAIL report with specialist findings |
| **Project Viewer** | `/dev-team-view-project <target>` | Generate a human-readable HTML view of a cookbook project and open it in the browser |

## Architecture

Three repos:
- **This repo (plugin)** — agents, skills, specialist research
- **agentic-cookbook** — upstream knowledge (principles, guidelines, compliance)
- **Workspace repo** — per-user data (profiles, transcripts, analyses, project builds)

## Repository Structure

```
.claude-plugin/            # Plugin manifest
agents/                    # 15 subagent definitions
skills/
  interview/               # Product discovery interview
  create-project-from-code/ # Codebase → cookbook project
  generate/                # Specialist recipe review
  build/                   # Cookbook project → working code
  lint/                    # Artifact linting against cookbook standards
  view-project/            # HTML project viewer
research/
  specialists/             # 19 specialist question sets (13 domain + 6 platform)
  cookbook-specialist-mapping.md
scripts/                   # Shell scripts for deterministic operations
planning/
  design-spec.md           # Full design specification
tests/                     # Test harness and personas
```

## Local Testing

Symlinks in `.claude/` point to top-level dirs for local testing. These are gitignored.

To test locally: `cd` into this repo and invoke `/dev-team-interview`.

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
