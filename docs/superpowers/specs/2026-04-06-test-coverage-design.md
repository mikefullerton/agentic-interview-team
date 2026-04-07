# Test Coverage Design

## Summary

Add pytest tests for the 6 uncovered areas of the dev-team plugin: Observers, Session scripts, Dashboard, Agents, Specialists, and Skills. Plus a deterministic Python test runner that iterates every area.

## Current State

2854 pytest tests across 5 areas (Arbitrator: 72, Project Storage: 64, Specialty Teams: 2626, Consulting Teams: 50, Test Harness: 42). Six areas have zero coverage. E2E tests (40, vitest) are out of scope for this spec.

## Test Files

```
tests/observers/test_observers.py
tests/session/test_session_scripts.py
tests/dashboard/test_dashboard.py
tests/agents/test_agents.py
tests/specialists/test_specialists.py
tests/skills/test_skills.py
tests/run_tests.py
```

Each file is self-contained. Each runs independently with `python3 -m pytest tests/<area>/`.

## Observers (~15 tests)

File: `tests/observers/test_observers.py`

### extract_event() unit tests

- Feed sample hook input dict with a real transcript JSONL temp file
- Verify normalized event has: timestamp, session_id, agent_type, agent_description, tools_used, tool_call_count, status, summary, duration_ms
- Edge cases: empty transcript, missing transcript file, transcript with no tool_use entries

### dispatch.py integration

- Write a tiny test observer module to a temp dir
- Pipe hook JSON to stdin via subprocess
- Verify the test observer's observe() was called with correct event

### stenographer.observe()

- Inject ARBITRATOR_SESSION_BASE to temp dir
- Call observe() with sample event
- Read session.log JSONL, verify fields: ts, sid, agent, desc, status, duration_ms, tools, calls, summary

### oslog.observe()

- Mock subprocess.run
- Call observe() with sample event
- Verify logger called with correct args and message format: `[dev-team] <type> "<desc>" <status> (<duration>s, <calls> calls)`

### session_paths.get_session_log_path()

- Existing session dir returns session_dir/session.log
- Missing session returns _logs/observer.log

## Session Scripts (~12 tests)

File: `tests/session/test_session_scripts.py`

### load_config.py

- Inject config path via env var
- Test loading valid config (returns parsed dict)
- Test missing config file (error)
- Test malformed JSON (error)

### version_check.py

- Test version comparison logic
- Current matches expected (pass)
- Current behind expected (warning/fail)
- Missing version file (error or graceful fallback)

### resume_session.py

- Inject session base to temp dir
- Create a session with state files
- Test resuming existing session (finds session, reads state)
- Test resuming nonexistent session (error)

## Dashboard (~20 tests)

File: `tests/dashboard/test_dashboard.py`

### db.py / models.py unit tests

- Create in-memory SQLite database
- Test CRUD operations on each model
- Test query methods return expected results

### API endpoint integration

- Use Flask test_client()
- Test each endpoint in api/workflows.py, api/messages.py, api/projects.py
- Valid requests return expected JSON structure
- Invalid requests return appropriate error responses
- Endpoints read from database layer, not hardcoded data

## Agents (~parametrized across 20 files)

File: `tests/agents/test_agents.py`

Per agent definition file:

- Has valid frontmatter (parses correctly)
- Has required fields: name, description
- name matches filename (without .md)
- name is kebab-case
- If tools present: is a YAML list
- If permissionMode present: is one of plan, full, bypassPermissions
- If maxTurns present: is a positive integer
- Body is non-empty (has actual agent instructions)
- No unknown frontmatter fields — every field present must be in the known set: name, description, tools, permissionMode, maxTurns, model

Known field set derived from scanning all 20 current agent files.

## Specialists (~parametrized across 21 files + assign_specialists tests)

File: `tests/specialists/test_specialists.py`

Per specialist definition file:

- Has ## Role section (non-empty)
- Has ## Cookbook Sources section (list of paths)
- Has ## Manifest section (paths resolve to existing files)
- Has ## Exploratory Prompts section (at least one numbered item)
- If ## Consulting Teams present: paths resolve to existing consulting-team files
- No ## Specialty Teams section (deprecated)

### assign_specialists.py

- Feed it a mock specialist directory
- Verify it returns correct specialist assignments
- Test with empty directory
- Test with nonexistent directory

## Skills (~15 tests)

File: `tests/skills/test_skills.py`

### SKILL.md validation

- Has frontmatter with name, description, version
- Version is semver
- Version string appears in body (Startup section consistency check)
- References to workflow files resolve to existing files

### Workflow file validation (parametrized across 8 files)

- File exists and is non-empty
- References to agent names (if any) match files in agents/
- References to specialist names (if any) match files in specialists/
- References to script paths (if any) match files in scripts/

## Test Runner

File: `tests/run_tests.py`

A Python script that iterates every test area deterministically:

```
python3 tests/run_tests.py
```

Runs pytest per area in fixed order:

1. arbitrator
2. project-storage
3. specialty-teams
4. consulting-teams
5. observers
6. session
7. dashboard
8. agents
9. specialists
10. skills
11. harness

Reports pass/fail/count per area. Prints summary table at the end. Exits non-zero if any area fails.

## Constraints

- All tests are Python/pytest. No TypeScript, no vitest, no shell scripts.
- Each test file is self-contained — no shared fixtures across areas.
- Tests use dependency injection (env vars, temp dirs, mocked subprocess) rather than modifying global state.
- Dashboard tests use Flask test_client() and in-memory SQLite.
- Observer tests mock subprocess for oslog and inject temp dirs for stenographer.

## Implementation Order

1. Agents (simplest — pure file validation, pattern identical to specialty-teams)
2. Specialists (similar pattern + assign_specialists.py)
3. Skills (similar pattern + cross-reference validation)
4. Observers (behavioral tests, moderate complexity)
5. Session scripts (behavioral tests, need to read each script first)
6. Dashboard (most complex — Flask test_client, db setup)
7. Test runner (depends on all areas existing)
