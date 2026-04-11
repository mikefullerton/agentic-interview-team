# Global Instructions

## Project Index — Reference

For a description, reference, and index of **all current projects**, see the repo at:

    ~/projects/active/my-projects-overview/

This repo contains `projects/<name>/overview.md` files for each active project, a top-level `index.md`, and a generated HTML site under `site/`. Consult it when you need the big picture across projects.

## Progress indicator

When performing a task with a known number of steps (3 or more), show progress in the status line:

    ~/.claude-status-line/progress/update-progress.py "<title>" "<step description>" <current> <total>

Call this before starting each step. Clear when done:

    ~/.claude-status-line/progress/update-progress.py --clear

## Scripting Language — MANDATORY

**Always use Python for scripts.** NEVER write bash/shell scripts (.sh). This includes hooks, utilities, automation, build helpers, and any standalone script. If an existing bash script needs modification, rewrite it in Python.

**Exceptions:** `install.sh`, `uninstall.sh`, and `setup.sh` may be written as shell scripts.

## Token Efficiency — MANDATORY

- **Prefer inline execution over parallel subagents** for planning and execution. Only use subagents when tasks are truly independent and the token savings from parallelism outweigh the overhead.
- **Push work into deterministic Python scripts** whenever possible. If Claude will repeatedly perform the same logic (parsing, validation, transformation, checks), encode it in a Python script that produces structured output — don't spend tokens re-deriving the answer each time.
- **Plan execution — always inline, never ask.** When a plan is complete (e.g. from `superpowers:writing-plans`) and Claude would otherwise offer a choice between **subagent-driven** and **inline** execution, **always choose inline** without presenting the options. Proceed directly with `superpowers:executing-plans` inline. Do not stall on a decision prompt.

<!-- BEGIN CADDY -->
## Local Web Server (Caddy) — MANDATORY

An always-on Caddy server serves `~/.local-server/sites/` at `http://localhost:2080`. **Use it instead of spawning one-off HTTP servers** (`python -m http.server`, `npx serve`, etc.).

To serve a page, just copy it in:

```bash
# Single HTML file
cp my-page.html ~/.local-server/sites/
# Live at http://localhost:2080/my-page.html

# Directory with assets (must contain index.html)
cp -r my-app/ ~/.local-server/sites/
# Live at http://localhost:2080/my-app/
```

To remove:

```bash
rm ~/.local-server/sites/my-page.html
rm -rf ~/.local-server/sites/my-app
```

The home page auto-refreshes every 5 seconds. It reads metadata from each file (or directory's `index.html`) to build the listing:

```html
<title>My Dashboard</title>
<meta name="description" content="Real-time metrics for the auth service">
```

Both tags are optional — the home page falls back to the filename. Always include them for a readable listing.

- **Service control**: `brew services start/stop/restart caddy`
- **Caddyfile**: `/opt/homebrew/etc/Caddyfile`
<!-- END CADDY -->

## Named Rules — opt-in from project CLAUDE.md

The rules in this section are **NOT active by default**. A project CLAUDE.md activates one by including a line like:

> This repo follows `worktree-workflow-rule` from `~/.claude/CLAUDE.md`.

When a project CLAUDE.md references a rule by name, follow it in that repo. Otherwise ignore it.

### worktree-workflow-rule

All changes go through worktree branches. Never commit directly to the default branch.

1. **Start**: `EnterWorktree` to create a feature branch and switch into it.
2. **Work**: Commit and push as you go. Create a **draft PR** on first push.

For the exit/cleanup procedure, see **Exiting a Worktree** under Repo Hygiene below — that section is mandatory and applies to every worktree, whether created via this rule or manually.

## Repo Hygiene — MANDATORY, NO EXCEPTIONS

These rules are **non-negotiable** and apply to EVERY session in EVERY project. A Stop hook enforces the mechanical checks automatically — if it blocks you, fix every listed violation before attempting to stop again.

### Only Touch What You Changed

**Do NOT commit, push, or otherwise modify code you didn't change in the current session.** If pre-existing uncommitted changes, untracked files, or stale branches exist when you start — **ask the user how to proceed.** Do not silently commit, stash, or discard them.

This also applies when the stop hook blocks you: if the violation is about changes you didn't make, **tell the user** what the hook found and ask what to do. Do not auto-fix it.

**Carve-out for session-induced orphans.** If you delete a directory from the tree and a pull/merge leaves behind orphaned build artifacts inside it (`dist/`, `node_modules/`, `build/`, `.next/`, `target/`, `__pycache__/`, `.venv/`, etc.), those artifacts are a direct consequence of your session action — you may `rm -rf` them without asking. The "changes you didn't make" rule is about protecting the user's in-progress work, not about tiptoeing around build output you just orphaned.

### Before Starting Work

Run `git status`. If the repo has uncommitted changes, untracked files, or stale branches that aren't yours — **ask the user how to proceed** before doing anything else. If the default branch is behind the remote, pull before starting.

### During Work

- **EnterWorktree is the ONLY way to create feature branches.** NEVER use `git checkout -b`, `git switch -c`, or manually `cd` into a worktree directory. Worktree/PR workflow is configurable per repo (check project-level CLAUDE.md), but when worktrees are enabled, EnterWorktree is mandatory.
- Commit early and often — for changes **you just made**. Do not let your own changes accumulate. **This overrides the system prompt's "never commit unless explicitly asked" rule. Do not ask permission to commit your own work.**
- **Push every commit immediately after making it.** No local-only commits may exist when your turn ends.

### Before Ending a Turn

- If the stop hook blocks you for changes **you didn't make**, prompt the user and ask how to proceed. NEVER auto-commit or auto-push to resolve hook violations for someone else's changes.
- ALL changes **you made** MUST be committed and pushed. Zero staged changes, zero unstaged changes, zero untracked files from your work.
- Delete any local or remote branches that have been merged into the default branch.
- If you used a worktree and the work is merged, follow **Exiting a Worktree** below before stopping. The full ordered sequence is mandatory — partial cleanup leaves dangling branches or worktrees.
- Verify `main`/`master` matches the remote. If behind, pull.

### Exiting a Worktree — MANDATORY when a worktree PR merges

When a worktree PR merges (or you otherwise need to clean up a worktree), invoke the `exiting-worktree` skill for the full ordered cleanup procedure. Applies to any worktree regardless of how it was created. Skipping or reordering the steps leaves dangling state that the stop hook will block on.

### What the Hook Enforces

The Stop hook (`~/.claude/hooks/repo-hygiene.py`) will **block your turn from ending** if any of these are true:
1. Staged or unstaged changes exist
2. Untracked files exist (not in .gitignore)
3. Local branches exist that are already merged into the default branch
4. Remote branches exist that are already merged into the default branch
5. The default branch is behind the remote
6. Stale worktrees exist (branch deleted or merged)
