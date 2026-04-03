# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Skills

| Command | Description |
|---------|-------------|
| `/dev-team interview` | Product discovery — structured and exploratory questioning with specialist expertise |
| `/dev-team create-project-from-code` | Reverse-engineer a codebase into a cookbook project |
| `/dev-team generate` | Specialist review and improvement of cookbook recipes |
| `/dev-team create-code-from-project` | Build working code from a cookbook project |
| `/dev-team lint` | Evaluate any artifact against cookbook standards |
| `/dev-team align-specialists` | Review specialist-cookbook alignment after guideline changes |
| `/dev-team compare-code` | Compare two code projects for round-trip verification |
| `/dev-team view-project` | Generate HTML view of a cookbook project |

## Setup

On first run, `/dev-team interview` creates `~/.agentic-cookbook/dev-team/config.json`:

```json
{
  "workspace_repo": "<path to your workspace repo>",
  "cookbook_repo": "<path to agentic-cookbook>",
  "user_name": "<your name>",
  "authorized_repos": []
}
```

## Architecture

Each skill orchestrates a team of specialist agents — domain experts (security, accessibility, UI/UX, architecture, etc.) and platform experts (iOS, Windows, Android, web, database).

### Three Repos

| Repo | Purpose |
|------|---------|
| **dev-team** (this plugin) | The system — agents, skills, specialists |
| **agentic-cookbook** | Upstream knowledge — principles, guidelines, compliance |
| **Workspace repo** | Per-user data — profiles, transcripts, analyses, project builds |

### Specialists

**Domain (13):** Security, Accessibility, Reliability, UI/UX & Design, Software Architecture, Testing & QA, Networking & API, Code Quality, DevOps & Observability, Localization & I18n, Development Process, Data & Persistence, Claude Code & Agentic Development

**Platform (6):** iOS / Apple Platforms, Windows, Android, Web Frontend, Web Backend / Services, Database

Each specialist manages **specialty-teams** — worker-verifier pairs focused on one cookbook artifact each. 186 total specialty-teams across 19 specialists.

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

## Local Development

To test locally, `cd` into this repo and invoke `/dev-team interview`.
