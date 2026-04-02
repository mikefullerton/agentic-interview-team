# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Skills

- `/dev-team:interview` — Product discovery interview
- `/dev-team:analyze-project` — Reverse-engineer codebase into cookbook project
- `/dev-team:generate-project` — Specialist recipe review
- `/dev-team:build-project` — Build working code from cookbook project

## Architecture

Three repos:
- **This repo (plugin)** — agents, skills, specialist research
- **agentic-cookbook** — upstream knowledge (principles, guidelines, compliance)
- **Workspace repo** — per-user data (profiles, transcripts, analyses, project builds)

## Repository Structure

```
.claude-plugin/            # Plugin manifest
agents/                    # 14 subagent definitions
skills/
  interview/               # Product discovery interview
  analyze-project/         # Codebase → cookbook project
  generate-project/        # Specialist recipe review
  build-project/           # Cookbook project → working code
research/
  specialists/             # 18 specialist question sets (12 domain + 6 platform)
  cookbook-specialist-mapping.md
planning/
  design-spec.md           # Full design specification
tests/                     # Test harness and personas
```

## Local Testing

Symlinks in `.claude/` point to top-level dirs for local testing. These are gitignored.

To test locally: `cd` into this repo and invoke `/interview`.

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
