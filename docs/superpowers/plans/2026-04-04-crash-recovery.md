# Crash Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add crash recovery to the specialist execution loop so interrupted sessions can resume mid-specialist, skipping completed specialty-teams.

**Architecture:** New `team-result` arbitrator resource tracks each specialty-team's status within a specialist's result. New `resume-session.sh` script detects interrupted sessions. Workflows call it at startup, prompt the user via a gate, and skip completed teams on resume.

**Tech Stack:** Bash shell scripts, jq for JSON, arbitrator markdown backend pattern.

**Design spec:** `docs/superpowers/specs/2026-04-04-crash-recovery-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `scripts/arbitrator/markdown/team-result.sh` | CRUD for team-result resource (create/get/list/update) |
| `scripts/resume-session.sh` | Detect interrupted sessions, report progress summary |
| `tests/arbitrator/contract/11-team-results.sh` | Contract tests for team-result resource |

### Modified Files

| File | Change |
|------|--------|
| `scripts/arbitrator/markdown/_lib.sh` | Add `--team`, `--iteration`, `--verifier-feedback` parse flags |
| `skills/dev-team/workflows/generate.md` | Add resume check at startup + team-result tracking in loop |
| `skills/dev-team/workflows/create-recipe-from-code.md` | Same pattern |
| `skills/dev-team/workflows/lint.md` | Same pattern |
| `docs/architecture.md` | Add team-result to arbitrator resources list |
| `docs/specialist-guide.md` | Add crash recovery section to execution flow |

---

## Task 1: Add parse flags to _lib.sh

**Files:**
- Modify: `scripts/arbitrator/markdown/_lib.sh:89-119`

- [ ] **Step 1: Add three new flags to parse_flags**

Add these initializations after line 87 (`PARSED_STATUS=""`):

```bash
PARSED_TEAM=""
PARSED_ITERATION=""
PARSED_VERIFIER_FEEDBACK=""
```

Add these cases inside the `while` loop after the `--status` case (line 116):

```bash
      --team) PARSED_TEAM="$2"; shift 2 ;;
      --iteration) PARSED_ITERATION="$2"; shift 2 ;;
      --verifier-feedback) PARSED_VERIFIER_FEEDBACK="$2"; shift 2 ;;
```

- [ ] **Step 2: Run existing arbitrator tests to verify no regression**

Run: `bash tests/arbitrator/run-contract-tests.sh`

Expected: All existing tests pass (the new flags don't affect existing behavior since they default to empty).

- [ ] **Step 3: Commit**

```bash
git add scripts/arbitrator/markdown/_lib.sh
git commit -m "Add team, iteration, verifier-feedback parse flags to arbitrator lib"
git push
```

---

## Task 2: Implement team-result.sh

**Files:**
- Create: `scripts/arbitrator/markdown/team-result.sh`

- [ ] **Step 1: Write the team-result resource script**

```bash
#!/bin/bash
# team-result.sh — Team-result resource for markdown arbitrator
# Actions: create, get, list, update
set -euo pipefail

source "$(dirname "$0")/_lib.sh"

ACTION="${1:?Usage: team-result.sh <create|get|list|update> [flags]}"; shift
parse_flags "$@"

case "$ACTION" in
  create)
    require_flag "session" "$PARSED_SESSION"
    require_flag "result" "$PARSED_RESULT"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAMS_DIR="${DIR}/results/${PARSED_SPECIALIST}/teams"
    mkdir -p "$TEAMS_DIR"

    TEAM_RESULT_ID="${PARSED_SESSION}:team-result:${PARSED_SPECIALIST}:${PARSED_TEAM}"
    TEAM_FILE="${TEAMS_DIR}/${PARSED_TEAM}.json"

    jq -n \
      --arg team_result_id "$TEAM_RESULT_ID" \
      --arg session_id "$PARSED_SESSION" \
      --arg result_id "$PARSED_RESULT" \
      --arg specialist "$PARSED_SPECIALIST" \
      --arg team_name "$PARSED_TEAM" \
      --arg status "running" \
      --argjson iteration 0 \
      --arg verifier_feedback "" \
      --arg creation_date "$(now_iso)" \
      --arg modification_date "$(now_iso)" \
      '{
        team_result_id: $team_result_id,
        session_id: $session_id,
        result_id: $result_id,
        specialist: $specialist,
        team_name: $team_name,
        status: $status,
        iteration: $iteration,
        verifier_feedback: $verifier_feedback,
        creation_date: $creation_date,
        modification_date: $modification_date
      }' > "$TEAM_FILE"

    json_build team_result_id="$TEAM_RESULT_ID"
    ;;

  get)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAM_FILE="${DIR}/results/${PARSED_SPECIALIST}/teams/${PARSED_TEAM}.json"

    if [[ ! -f "$TEAM_FILE" ]]; then
      echo "Team-result not found: ${PARSED_SPECIALIST}/${PARSED_TEAM}" >&2
      exit 1
    fi

    cat "$TEAM_FILE"
    ;;

  list)
    require_flag "session" "$PARSED_SESSION"

    DIR="$(require_session "$PARSED_SESSION")"
    RESULTS_BASE="${DIR}/results"

    if [[ ! -d "$RESULTS_BASE" ]]; then
      echo "[]"
      exit 0
    fi

    OUTPUT="[]"
    for team_file in "${RESULTS_BASE}"/*/teams/*.json; do
      [[ -f "$team_file" ]] || continue

      if [[ -n "$PARSED_SPECIALIST" ]]; then
        FILE_SPECIALIST=$(jq -r '.specialist' "$team_file")
        [[ "$FILE_SPECIALIST" == "$PARSED_SPECIALIST" ]] || continue
      fi

      if [[ -n "$PARSED_STATUS" ]]; then
        FILE_STATUS=$(jq -r '.status' "$team_file")
        [[ "$FILE_STATUS" == "$PARSED_STATUS" ]] || continue
      fi

      OUTPUT=$(echo "$OUTPUT" | jq --argjson obj "$(cat "$team_file")" '. + [$obj]')
    done

    echo "$OUTPUT"
    ;;

  update)
    require_flag "session" "$PARSED_SESSION"
    require_flag "specialist" "$PARSED_SPECIALIST"
    require_flag "team" "$PARSED_TEAM"

    DIR="$(require_session "$PARSED_SESSION")"
    TEAM_FILE="${DIR}/results/${PARSED_SPECIALIST}/teams/${PARSED_TEAM}.json"

    if [[ ! -f "$TEAM_FILE" ]]; then
      echo "Team-result not found: ${PARSED_SPECIALIST}/${PARSED_TEAM}" >&2
      exit 1
    fi

    UPDATED=$(cat "$TEAM_FILE")

    if [[ -n "$PARSED_STATUS" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --arg v "$PARSED_STATUS" '.status = $v')
    fi

    if [[ -n "$PARSED_ITERATION" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --argjson v "$PARSED_ITERATION" '.iteration = $v')
    fi

    if [[ -n "$PARSED_VERIFIER_FEEDBACK" ]]; then
      UPDATED=$(echo "$UPDATED" | jq --arg v "$PARSED_VERIFIER_FEEDBACK" '.verifier_feedback = $v')
    fi

    UPDATED=$(echo "$UPDATED" | jq --arg v "$(now_iso)" '.modification_date = $v')

    echo "$UPDATED" > "$TEAM_FILE"

    json_build team_result_id="$(echo "$UPDATED" | jq -r '.team_result_id')"
    ;;

  *)
    echo "Unknown action: ${ACTION}" >&2
    echo "Usage: team-result.sh <create|get|list|update> [flags]" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/arbitrator/markdown/team-result.sh`

- [ ] **Step 3: Commit**

```bash
git add scripts/arbitrator/markdown/team-result.sh
git commit -m "Add team-result arbitrator resource

Tracks specialty-team outcomes within a specialist's result.
Actions: create, get, list (with specialist/status filters), update.
Stored at sessions/<id>/results/<specialist>/teams/<team>.json."
git push
```

---

## Task 3: Write contract tests for team-result

**Files:**
- Create: `tests/arbitrator/contract/11-team-results.sh`

- [ ] **Step 1: Write the contract test file**

```bash
#!/bin/bash
# 11-team-results.sh — Contract tests for team-result resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Setup --

make_session() {
  "$ARBITRATOR" session create \
    --playbook generate \
    --team-lead review \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id'
}

make_result() {
  local session_id="$1" specialist="$2"
  "$ARBITRATOR" result create \
    --session "$session_id" \
    --specialist "$specialist" \
    | jq -r '.result_id'
}

# -- Tests --

test_team_result_create_returns_id() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  OUTPUT=$("$ARBITRATOR" team-result create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --team authentication)
  TR_ID=$(echo "$OUTPUT" | jq -r '.team_result_id')
  assert_not_empty "$TR_ID" "team_result_id"
}

test_team_result_create_sets_running_status() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  "$ARBITRATOR" team-result create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --team authorization > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result get \
    --session "$SESSION_ID" \
    --specialist security \
    --team authorization)
  assert_json_field "$OUTPUT" '.status' "running"
  assert_json_field "$OUTPUT" '.iteration' "0"
  assert_json_field "$OUTPUT" '.specialist' "security"
  assert_json_field "$OUTPUT" '.team_name' "authorization"
}

test_team_result_update_status_and_iteration() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  "$ARBITRATOR" team-result create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --team token-handling > /dev/null

  "$ARBITRATOR" team-result update \
    --session "$SESSION_ID" \
    --specialist security \
    --team token-handling \
    --status passed \
    --iteration 2 > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result get \
    --session "$SESSION_ID" \
    --specialist security \
    --team token-handling)
  assert_json_field "$OUTPUT" '.status' "passed"
  assert_json_field "$OUTPUT" '.iteration' "2"
}

test_team_result_update_verifier_feedback() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  "$ARBITRATOR" team-result create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --team cors > /dev/null

  "$ARBITRATOR" team-result update \
    --session "$SESSION_ID" \
    --specialist security \
    --team cors \
    --status failed \
    --iteration 1 \
    --verifier-feedback "Missing CORS allowlist check" > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result get \
    --session "$SESSION_ID" \
    --specialist security \
    --team cors)
  assert_json_field "$OUTPUT" '.status' "failed"
  assert_json_field "$OUTPUT" '.verifier_feedback' "Missing CORS allowlist check"
}

test_team_result_list_all_for_specialist() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$RESULT_ID" --specialist security --team authentication > /dev/null
  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$RESULT_ID" --specialist security --team authorization > /dev/null
  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$RESULT_ID" --specialist security --team cors > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result list --session "$SESSION_ID" --specialist security)
  assert_json_count "$OUTPUT" "3" "should have 3 team-results for security"
}

test_team_result_list_filters_by_status() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "security")

  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$RESULT_ID" --specialist security --team authentication > /dev/null
  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$RESULT_ID" --specialist security --team authorization > /dev/null

  "$ARBITRATOR" team-result update --session "$SESSION_ID" --specialist security --team authentication --status passed --iteration 1 > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result list --session "$SESSION_ID" --specialist security --status passed)
  assert_json_count "$OUTPUT" "1" "should have 1 passed team-result"
  assert_json_field "$OUTPUT" '.[0].team_name' "authentication"
}

test_team_result_list_filters_by_specialist() {
  SESSION_ID=$(make_session)
  SEC_RESULT=$(make_result "$SESSION_ID" "security")
  ACC_RESULT=$(make_result "$SESSION_ID" "accessibility")

  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$SEC_RESULT" --specialist security --team authentication > /dev/null
  "$ARBITRATOR" team-result create --session "$SESSION_ID" --result "$ACC_RESULT" --specialist accessibility --team accessibility > /dev/null

  OUTPUT=$("$ARBITRATOR" team-result list --session "$SESSION_ID" --specialist security)
  assert_json_count "$OUTPUT" "1" "should have 1 team-result for security"
}

test_team_result_list_empty_session() {
  SESSION_ID=$(make_session)

  OUTPUT=$("$ARBITRATOR" team-result list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "0" "should have 0 team-results"
}

test_team_result_get_nonexistent_fails() {
  SESSION_ID=$(make_session)
  make_result "$SESSION_ID" "security" > /dev/null

  if "$ARBITRATOR" team-result get --session "$SESSION_ID" --specialist security --team nonexistent 2>/dev/null; then
    echo "Expected failure for nonexistent team-result" >&2
    return 1
  fi
}

test_team_result_update_nonexistent_fails() {
  SESSION_ID=$(make_session)
  make_result "$SESSION_ID" "security" > /dev/null

  if "$ARBITRATOR" team-result update --session "$SESSION_ID" --specialist security --team nonexistent --status passed 2>/dev/null; then
    echo "Expected failure for nonexistent team-result" >&2
    return 1
  fi
}

# -- Run --

run_test "team-result create returns team_result_id" test_team_result_create_returns_id
run_test "team-result create sets running status and iteration 0" test_team_result_create_sets_running_status
run_test "team-result update changes status and iteration" test_team_result_update_status_and_iteration
run_test "team-result update stores verifier feedback" test_team_result_update_verifier_feedback
run_test "team-result list returns all for specialist" test_team_result_list_all_for_specialist
run_test "team-result list filters by status" test_team_result_list_filters_by_status
run_test "team-result list filters by specialist" test_team_result_list_filters_by_specialist
run_test "team-result list returns empty for new session" test_team_result_list_empty_session
run_test "team-result get nonexistent fails" test_team_result_get_nonexistent_fails
run_test "team-result update nonexistent fails" test_team_result_update_nonexistent_fails

test_summary
```

- [ ] **Step 2: Run the tests**

Run: `bash tests/arbitrator/run-contract-tests.sh`

Expected: All 11 test suites pass, including the new `11-team-results` suite with 10 tests.

- [ ] **Step 3: Fix any failures and re-run until green**

- [ ] **Step 4: Commit**

```bash
git add tests/arbitrator/contract/11-team-results.sh
git commit -m "Add contract tests for team-result arbitrator resource

10 tests covering: create, get, list (with specialist/status filters),
update (status, iteration, verifier feedback), error cases."
git push
```

---

## Task 4: Implement resume-session.sh

**Files:**
- Create: `scripts/resume-session.sh`

- [ ] **Step 1: Write the resume-session script**

```bash
#!/bin/bash
# resume-session.sh — Detect interrupted sessions for a given playbook
# Usage: resume-session.sh --playbook <name>
#
# Output: JSON with interrupted session info or {"interrupted": false}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARBITRATOR="$SCRIPT_DIR/arbitrator.sh"

PLAYBOOK=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --playbook) PLAYBOOK="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$PLAYBOOK" ]]; then
  echo "Usage: resume-session.sh --playbook <name>" >&2
  exit 1
fi

# Find sessions for this playbook with status "running" (never completed)
SESSIONS=$("$ARBITRATOR" session list --playbook "$PLAYBOOK" --status running 2>/dev/null || echo "[]")
SESSION_COUNT=$(echo "$SESSIONS" | jq 'length')

if [[ "$SESSION_COUNT" -eq 0 ]]; then
  echo '{"interrupted": false}'
  exit 0
fi

# Use the most recent interrupted session
SESSION=$(echo "$SESSIONS" | jq '.[-1]')
SESSION_ID=$(echo "$SESSION" | jq -r '.session_id')
CREATION_DATE=$(echo "$SESSION" | jq -r '.creation_date')

# Build specialist progress summary
RESULTS=$("$ARBITRATOR" result list --session "$SESSION_ID" 2>/dev/null || echo "[]")
SPECIALISTS="[]"

for row in $(echo "$RESULTS" | jq -c '.[]'); do
  SPECIALIST=$(echo "$row" | jq -r '.specialist')

  TEAM_RESULTS=$("$ARBITRATOR" team-result list --session "$SESSION_ID" --specialist "$SPECIALIST" 2>/dev/null || echo "[]")
  TOTAL=$(echo "$TEAM_RESULTS" | jq 'length')
  COMPLETED=$(echo "$TEAM_RESULTS" | jq '[.[] | select(.status == "passed" or .status == "escalated")] | length')
  ESCALATED=$(echo "$TEAM_RESULTS" | jq '[.[] | select(.status == "escalated")] | length')

  SPECIALISTS=$(echo "$SPECIALISTS" | jq \
    --arg name "$SPECIALIST" \
    --argjson completed "$COMPLETED" \
    --argjson total "$TOTAL" \
    --argjson escalated "$ESCALATED" \
    '. + [{"name": $name, "teams_completed": $completed, "teams_total": $total, "teams_escalated": $escalated}]')
done

jq -n \
  --argjson interrupted true \
  --arg session_id "$SESSION_ID" \
  --arg creation_date "$CREATION_DATE" \
  --argjson specialists "$SPECIALISTS" \
  '{interrupted: $interrupted, session_id: $session_id, creation_date: $creation_date, specialists: $specialists}'
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/resume-session.sh`

- [ ] **Step 3: Commit**

```bash
git add scripts/resume-session.sh
git commit -m "Add resume-session.sh for interrupted session detection

Queries arbitrator for running sessions matching a playbook, builds
specialist progress summary from team-result data. Outputs JSON."
git push
```

---

## Task 5: Update generate.md workflow

**Files:**
- Modify: `skills/dev-team/workflows/generate.md`

- [ ] **Step 1: Read the current generate.md to identify insertion points**

Read `skills/dev-team/workflows/generate.md` — specifically the startup section (before Phase 1) and the specialty-team loop (Phase 3b).

- [ ] **Step 2: Add resume check after DB init, before Phase 1**

Insert after the config loading / DB init section, before Phase 1:

```markdown
### Resume Check

Call `${CLAUDE_PLUGIN_ROOT}/scripts/resume-session.sh --playbook generate`. If the output has `"interrupted": true`:

1. Present a gate to the user via the arbitrator:
   - Message: "Found interrupted generate session from `<creation_date>` with progress: `<specialist summaries>`. Resume or restart?"
   - Options: "Resume" (reuse session), "Restart" (abandon old, create new)
2. If user picks Resume: use the returned `session_id` for this run. Skip creating a new session.
3. If user picks Restart: mark the old session as `abandoned` via `arbitrator.sh state append --session <old-id> --changed-by team-lead --state abandoned --description "User chose restart"`. Create a new session normally.
```

- [ ] **Step 3: Add team-result tracking to the specialty-team loop**

In Phase 3b (the specialty-team loop), update the iteration instructions:

Before spawning the worker, add:

```markdown
**Check for existing team-result**: Query `arbitrator.sh team-result list --session $SESSION_ID --specialist <domain>`. For each team in the manifest:
- If the team has `status: passed` or `status: escalated`: skip it.
- If the team has `status: failed`: resume at iteration N+1 with the stored `verifier_feedback` as Previous feedback.
- If the team has `status: running`: re-run from iteration 1 (crashed mid-execution).
- If not present: create a new team-result with `arbitrator.sh team-result create --session $SESSION_ID --result $RESULT_ID --specialist <domain> --team <name>`.
```

After the worker-verifier loop outcome, add:

```markdown
**Record team outcome**: 
- On PASS: `arbitrator.sh team-result update --session $SESSION_ID --specialist <domain> --team <name> --status passed --iteration <N>`
- On FAIL (will retry): `arbitrator.sh team-result update --session $SESSION_ID --specialist <domain> --team <name> --status failed --iteration <N> --verifier-feedback "<reasons>"`
- On escalation: `arbitrator.sh team-result update --session $SESSION_ID --specialist <domain> --team <name> --status escalated --iteration 3`
```

- [ ] **Step 4: Commit**

```bash
git add skills/dev-team/workflows/generate.md
git commit -m "Add crash recovery to generate workflow

Resume check at startup detects interrupted sessions, presents
gate to user. Team-result tracking in the specialty-team loop
enables skipping completed teams on resume."
git push
```

---

## Task 6: Update create-recipe-from-code.md workflow

**Files:**
- Modify: `skills/dev-team/workflows/create-recipe-from-code.md`

- [ ] **Step 1: Read the current workflow to identify the specialty-team loop**

Read `skills/dev-team/workflows/create-recipe-from-code.md` — find where specialists are dispatched and the team loop runs.

- [ ] **Step 2: Add the same resume check and team-result tracking pattern**

Add the same resume check after config/DB init (using `--playbook create-recipe-from-code`).

Add the same team-result create/update/skip pattern around the specialist code pass loop.

The exact insertion points depend on the workflow's phase structure — read the file and apply the same pattern as Task 5 at the corresponding locations.

- [ ] **Step 3: Commit**

```bash
git add skills/dev-team/workflows/create-recipe-from-code.md
git commit -m "Add crash recovery to create-recipe-from-code workflow

Same resume check + team-result tracking pattern as generate."
git push
```

---

## Task 7: Update lint.md workflow

**Files:**
- Modify: `skills/dev-team/workflows/lint.md`

- [ ] **Step 1: Read the current workflow**

Read `skills/dev-team/workflows/lint.md` — find the specialty-team loop.

- [ ] **Step 2: Add resume check and team-result tracking**

Same pattern as Tasks 5 and 6, using `--playbook lint`.

- [ ] **Step 3: Commit**

```bash
git add skills/dev-team/workflows/lint.md
git commit -m "Add crash recovery to lint workflow

Same resume check + team-result tracking pattern as generate."
git push
```

---

## Task 8: Update docs

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/specialist-guide.md`

- [ ] **Step 1: Update architecture.md**

In the Arbitrator section, add `team-result` to the **Resources** list (line 101):

Change:
```
**Resources**: session, state, message, gate-option, result, finding, interpretation, artifact, reference, retry, report
```
To:
```
**Resources**: session, state, message, gate-option, result, finding, interpretation, artifact, reference, retry, report, team-result
```

- [ ] **Step 2: Update specialist-guide.md execution flow**

After the existing "Execution Flow" section (around line 87-100), add a new subsection:

```markdown
### Crash Recovery

If a session crashes mid-specialist, the system can resume on the next run:

1. At workflow startup, `scripts/resume-session.sh` checks for interrupted sessions
2. If found, the team-lead presents a gate: "Resume or restart?"
3. On resume, the orchestrator queries `team-result list` for the specialist
4. Teams with `status: passed` or `status: escalated` are skipped
5. Teams with `status: failed` resume at the next retry iteration with stored verifier feedback
6. Teams with `status: running` (crashed mid-execution) re-run from scratch

Team-results are recorded via the arbitrator (`arbitrator.sh team-result create/update`) as each team progresses through the worker-verifier loop.
```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.md docs/specialist-guide.md
git commit -m "Document crash recovery in architecture and specialist guide

Add team-result to arbitrator resources list. Add crash recovery
section to specialist execution flow documentation."
git push
```

---

## Task 9: Run full test suite and verify

- [ ] **Step 1: Run all arbitrator contract tests**

Run: `bash tests/arbitrator/run-contract-tests.sh`

Expected: All 11 suites pass, 0 failures. The new `11-team-results` suite should show 10/10 passed.

- [ ] **Step 2: Verify resume-session.sh works end-to-end**

Create a test session, add some team-results, and verify the script detects it:

```bash
# Create a session (will be in "running" state since we don't complete it)
SID=$(scripts/arbitrator.sh session create --playbook generate --team-lead review --user test --machine test | jq -r '.session_id')

# Add a state transition
scripts/arbitrator.sh state append --session "$SID" --changed-by team-lead --state reviewing --description "test"

# Create a result and some team-results
RID=$(scripts/arbitrator.sh result create --session "$SID" --specialist security | jq -r '.result_id')
scripts/arbitrator.sh team-result create --session "$SID" --result "$RID" --specialist security --team authentication
scripts/arbitrator.sh team-result update --session "$SID" --specialist security --team authentication --status passed --iteration 1
scripts/arbitrator.sh team-result create --session "$SID" --result "$RID" --specialist security --team authorization

# Now check resume detection
scripts/resume-session.sh --playbook generate
```

Expected output: JSON showing `interrupted: true`, session_id, and security specialist with 1 completed team out of 2.

- [ ] **Step 3: Clean up test data**

```bash
rm -rf ~/.agentic-cookbook/dev-team/sessions/$SID
```

- [ ] **Step 4: Commit (if any fixes were needed)**

```bash
git push
```
