# Crash Recovery for Specialist Execution

## Why

When a session crashes mid-specialist (during the specialty-team worker-verifier loop), all in-progress work for that specialist is lost. The orchestrator's conversation context disappears, and on the next run everything re-executes from scratch. For a specialist like security with 15 teams averaging 2-3 iterations each, that's significant wasted work.

The arbitrator already tracks session-level state and per-specialist results, but nothing at the specialty-team level. This design adds team-level tracking so the system can resume mid-specialist after a crash.

## Scope

- All workflows that use the specialty-team loop: `generate`, `create-code-from-project`, `lint`
- New arbitrator resource: `team-result`
- New shared script: `resume-session.sh`
- Workflow changes to track team progress and check for interrupted sessions on startup

## Design

### New Arbitrator Resource: `team-result`

Tracks each specialty-team's outcome within a specialist's result.

**Actions:**

| Action | Purpose |
|--------|---------|
| `create` | Record that a team is starting |
| `get` | Retrieve a specific team-result |
| `list` | List team-results for a session, filtered by specialist and/or status |
| `update` | Update status, iteration count, verifier feedback |

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `team_result_id` | string | Composite: `<session>:team-result:<specialist>:<team-name>` |
| `session_id` | string | Parent session |
| `result_id` | string | Parent specialist result |
| `specialist` | string | Specialist domain (e.g., `security`) |
| `team_name` | string | Specialty-team name (e.g., `authentication`) |
| `status` | string | `running`, `passed`, `failed`, `escalated` |
| `iteration` | integer | Current retry count (1-3) |
| `verifier_feedback` | string | Last verifier failure reasons (for resume mid-retry) |
| `creation_date` | string | ISO timestamp |
| `modification_date` | string | ISO timestamp, updated on each `update` |

**Markdown backend storage:**
```
sessions/<session-id>/results/<specialist>/teams/<team-name>.json
```

**CLI examples:**
```bash
# Team starting
arbitrator.sh team-result create \
  --session $SID --result $RID --specialist security --team authentication

# Verifier returned PASS on iteration 2
arbitrator.sh team-result update \
  --id "$SID:team-result:security:authentication" \
  --status passed --iteration 2

# Verifier returned FAIL on iteration 1
arbitrator.sh team-result update \
  --id "$SID:team-result:security:authentication" \
  --status failed --iteration 1 \
  --verifier-feedback "Missing PKCE code_challenge validation"

# Escalated after 3 failures
arbitrator.sh team-result update \
  --id "$SID:team-result:security:authentication" \
  --status escalated --iteration 3

# List completed teams for a specialist
arbitrator.sh team-result list --session $SID --specialist security --status passed

# List all teams for a specialist (for resume logic)
arbitrator.sh team-result list --session $SID --specialist security
```

### New Script: `resume-session.sh`

Deterministic script that detects interrupted sessions for a given playbook. No user interaction — the workflow handles that via the arbitrator's gate mechanism.

**Usage:** `resume-session.sh --playbook <name>`

**Output (interrupted session found):**
```json
{
  "interrupted": true,
  "session_id": "abc-123",
  "creation_date": "2026-04-04T10:30:00Z",
  "specialists": [
    {"name": "security", "teams_completed": 8, "teams_total": 15, "teams_escalated": 0},
    {"name": "accessibility", "teams_completed": 2, "teams_total": 2, "teams_escalated": 0}
  ]
}
```

**Output (no interrupted session):**
```json
{"interrupted": false}
```

**Detection logic:**
1. Call `arbitrator.sh session list --playbook <name> --status running`
2. A session whose latest state is `running` (never transitioned to `completed` or `interrupted`) is interrupted
3. For each interrupted session, query `arbitrator.sh team-result list --session <id>` and `arbitrator.sh result list --session <id>` to build the progress summary
4. Return the most recent interrupted session (if multiple exist)

### Workflow Integration

Each workflow adds the same pattern at two points.

**At startup:**
1. Call `resume-session.sh --playbook <name>`
2. If `interrupted: true`:
   - Present gate to user via arbitrator: "Found interrupted session from `<date>` with `<N>` specialists partially complete. Resume or restart?"
   - Gate options: `resume` (reuse session), `restart` (abandon old, create new)
3. If user picks resume: use the existing session ID, query team-results to know what to skip
4. If user picks restart: mark old session as `abandoned` via `arbitrator.sh state append`, create new session

**Inside the specialty-team loop (per team):**
1. **Before spawning worker:** Check if team-result already exists with `status: passed` or `status: escalated` — if so, skip this team
2. **Before spawning worker:** Create or update team-result with `status: running`
3. **After verifier PASS:** Update team-result with `status: passed`, current iteration
4. **After verifier FAIL (will retry):** Update team-result with `status: failed`, current iteration, verifier feedback
5. **After 3 failures:** Update team-result with `status: escalated`, iteration 3
6. **On resume with `status: running`:** This team crashed mid-execution — re-run from iteration 1 (or from last recorded iteration if verifier_feedback is present)

### Resume Behavior by Team Status

| Status on resume | Action |
|-----------------|--------|
| `passed` | Skip — work is done |
| `escalated` | Skip — already gave up |
| `failed` | Re-run worker at iteration N+1 with stored verifier feedback (e.g., failed at iteration 1 means resume at iteration 2 with the feedback that caused the failure) |
| `running` | Re-run from iteration 1 (crashed mid-execution, output unreliable) |
| Not present | Run normally (never started) |

## Files Changed

| File | Change |
|------|--------|
| `scripts/arbitrator/markdown/team-result.sh` | **New** — create/get/list/update |
| `scripts/arbitrator/markdown/_lib.sh` | Add parse flags: `--team`, `--iteration`, `--verifier-feedback` |
| `scripts/resume-session.sh` | **New** — detect interrupted sessions |
| `skills/dev-team/workflows/generate.md` | Add resume check + team-result tracking |
| `skills/dev-team/workflows/create-code-from-project.md` | Same pattern |
| `skills/dev-team/workflows/lint.md` | Same pattern |
| `tests/arbitrator/` | **New** — contract tests for team-result |
| `docs/architecture.md` | Add team-result to arbitrator resources |
| `docs/specialist-guide.md` | Add crash recovery to execution flow |

## Files NOT Changed

- Agent definitions (worker/verifier are unaware of crash recovery)
- `scripts/run-specialty-teams.sh` (JSON output unchanged)
- Existing arbitrator resources (result, finding, retry — no contract changes)
- `scripts/arbitrator.sh` (dispatcher already routes any resource)

## Verification

1. **Unit tests for `team-result` resource**: contract tests following the pattern in `tests/arbitrator/` — create, get, list with filters, update status transitions
2. **Integration test**: simulate a crash by creating a session, recording some team-results as passed and one as running, then calling `resume-session.sh` and verifying the output
3. **Manual test**: run `/dev-team generate`, kill the session mid-specialist, re-run and verify the resume gate appears with correct progress
