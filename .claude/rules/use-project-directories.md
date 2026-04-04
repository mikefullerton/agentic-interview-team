# Use Project Directories

The plugin is self-enclosed in `plugins/dev-team/`. Development tooling stays at the repo root.

## Plugin runtime files (`plugins/dev-team/`)

- **Agent definitions** go in `plugins/dev-team/agents/`
- **Specialist definitions** go in `plugins/dev-team/specialists/`
- **Specialty-team definitions** go in `plugins/dev-team/specialty-teams/<category>/`
- **Skills** go in `plugins/dev-team/skills/<skill-name>/`
- **Scripts** go in `plugins/dev-team/scripts/`
- **Services** go in `plugins/dev-team/services/<service-name>/`
- **Runtime docs** (specialist spec, guide, research) go in `plugins/dev-team/docs/`

## Development tooling (repo root)

- **Design specs and planning documents** go in `docs/planning/`
- **Architecture reference** is `docs/architecture.md`
- **Contract tests** go in `tests/arbitrator/` and `tests/project-storage/`
- **Test harness** goes in `tests/harness/`
- **Local dev skills** go in `.claude/skills/`

Always use the project's existing directories. Do not invent new top-level directories without asking.
