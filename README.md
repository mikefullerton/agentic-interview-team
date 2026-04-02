# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **interview** | `/dev-team interview` | Product discovery — structured and exploratory questioning to fully scope a product |
| **create-project-from-code** | `/dev-team create-project-from-code` | Reverse-engineer a codebase into a cookbook project |
| **generate** | `/dev-team generate` | Specialist review and improvement of cookbook recipes |
| **create-code-from-project** | `/dev-team create-code-from-project` | Build working code from a cookbook project |

## Installation

```bash
claude plugin marketplace add ~/projects/agentic-cookbook
claude plugin install dev-team@agentic-cookbook
```

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

If you have an existing config at `~/.agentic-interviewer/config.json`, it will be migrated automatically.

## Architecture

Each skill orchestrates a team of specialist agents — domain experts (security, accessibility, UI/UX, architecture, etc.) and platform experts (iOS, Windows, Android, web, database).

### Three Repos

| Repo | Purpose |
|------|---------|
| **dev-team** (this plugin) | The system — agents, skills, specialist research |
| **agentic-cookbook** | Upstream knowledge — principles, guidelines, compliance |
| **Workspace repo** | Per-user data — profiles, transcripts, analyses, project builds |

### Specialists

**Domain (12):** Security, Accessibility, Reliability, UI/UX & Design, Software Architecture, Testing & QA, Networking & API, Code Quality, DevOps & Observability, Localization & I18n, Development Process, Data & Persistence

**Platform (6):** iOS / Apple Platforms, Windows, Android, Web Frontend, Web Backend / Services, Database

## Repository Structure

```
.claude-plugin/            # Plugin manifest
agents/                    # 14 subagent definitions
skills/
  interview/               # Product discovery interview
  analyze/                 # Codebase → cookbook project
  generate/                # Specialist recipe review
  build/                   # Cookbook project → working code
research/
  specialists/             # 18 specialist question sets (12 domain + 6 platform)
  cookbook-specialist-mapping.md
planning/
  design-spec.md           # Full design specification
tests/                     # Test harness and personas
```

## Local Development

Symlinks in `.claude/` point to top-level dirs for local testing (gitignored). To test locally without installing the plugin, `cd` into this repo and invoke `/interview`.
