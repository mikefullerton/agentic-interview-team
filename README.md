
** WARNING: Under active development and not ready for general use yet, stay tuned!! **

# The Agentic Cookbook Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

## Quick Start

On first run, `/dev-team interview` creates `~/.agentic-cookbook/dev-team/config.json`:

```json
{
  "workspace_repo": "<path to your workspace repo>",
  "cookbook_repo": "<path to agentic-cookbook>",
  "user_name": "<your name>",
  "authorized_repos": []
}
```

To test locally, `cd` into this repo and invoke `/dev-team interview`.

## Documentation

- **[Architecture](docs/architecture.md)** — single source of truth for system design, terminology, components, data flow, subcommands, and file map
- **[Specialist Spec](docs/specialist-spec.md)** — formal specification for specialist definition files
- **[Specialist Guide](docs/specialist-guide.md)** — how specialists and specialty-teams work
