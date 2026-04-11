# Project Clones

All projects live in `~/projects/`.

## Clone Commands (for new machine)

```bash
# Infrastructure
git clone git@github.com:Shared-Project-Helpers/workflows.git ~/projects/workflows
git clone git@github.com:Shared-Project-Helpers/code-review-pipeline-test.git ~/projects/code-review-pipeline-test

# Parallel dev clones (QualityTime)
for i in 1 2 3 4; do git clone git@github.com:QualityTimeStudios/QualityTime.git ~/projects/QualityTime$i; done

# Parallel dev clones (Temporal)
for i in 1 2 3 4; do git clone git@github.com:temporal-company/temporal.git ~/projects/temporal$i; done

# Personal sites
git clone git@github.com:mikefullerton/mikefullerton.com.git ~/projects/active/mikefullerton.com
git clone git@github.com:mikefullerton/mikeisdrumming.git ~/projects/paused/mikeisdrumming
git clone git@github.com:mikefullerton/scratchyfish.com.git ~/projects/paused/scratchyfish.com

# Tools
git clone git@github.com:mikefullerton/market-research.git ~/projects/paused/market-research
```

## Duplicate Clones (same remote)

| Clones | Remote | Notes |
|--------|--------|-------|
| QualityTime1-4 | `QualityTimeStudios/QualityTime` | KMP cross-platform app (Compose Multiplatform, SwiftUI, React+TS, Ktor+PostgreSQL) |
| temporal1-4 | `temporal-company/temporal` | KMP cross-platform app + IoT module (same stack as QualityTime) |

When making changes to a shared repo, pick one clone, create a branch, push, open PR, merge, then `git pull` on all clones. The 1-4 numbering enables parallel Claude Code sessions without branch conflicts.

## Unique Projects

| Directory | Remote | Default Branch | Description |
|-----------|--------|---------------|-------------|
| code-review-pipeline-test | `Shared-Project-Helpers/code-review-pipeline-test` | main | KMP scaffold for testing the 8-agent review pipeline |
| workflows | `Shared-Project-Helpers/workflows` | main | Reusable GH Actions workflows (8 Claude agents) |
| market-research | `mikefullerton/market-research` | main | Python CLI — AI market research agent (Anthropic + Tavily) |
| mikefullerton.com | `mikefullerton/mikefullerton.com` | **gh-pages** | Personal portfolio (static HTML/CSS) |
| mikeisdrumming | `mikefullerton/mikeisdrumming` | main | Drumming site (static, has music API research) |
| scratchyfish.com | `mikefullerton/scratchyfish.com` | main | Blog/music site (Jekyll) |

## GitHub Organizations

| Org | Repos |
|-----|-------|
| `Shared-Project-Helpers` | workflows, code-review-pipeline-test, dotfiles |
| `QualityTimeStudios` | QualityTime |
| `temporal-company` | temporal |
| `mikefullerton` | mikefullerton.com, mikeisdrumming, scratchyfish.com, market-research |

## CLAUDE.md Status

- **Global rules** (`~/.claude/CLAUDE.md` symlinked from `~/.dotfiles/claude/CLAUDE.md`) — branch per session, commit as you go, auto-open PRs, always link PRs, config-only auto-merge. Projects inherit these and should NOT duplicate them.
- code-review-pipeline-test has detailed CLAUDE.md with pipeline docs and project structure.
- QualityTime and temporal have project-specific CLAUDE.md (KMP conventions, architecture decisions).
- workflows has CLAUDE.md with agent descriptions.
- mikefullerton.com has minimal CLAUDE.md (auto-merge all PRs).
- mikeisdrumming, scratchyfish.com have no project-level CLAUDE.md.

## Open PRs (as of Feb 2026)

- code-review-pipeline-test: PR #55 (test-runner auto tests), PR #11 (API client feature)

## Pending Work (not pushed/committed)

- mikeisdrumming: 1 unpushed commit (music API research) + untracked CNAME/index.html
