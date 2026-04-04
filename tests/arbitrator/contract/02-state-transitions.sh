#!/bin/bash
# 02-state-transitions.sh — Contract tests for state resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Helper --

new_session() {
  "$ARBITRATOR" session create \
    --playbook interview \
    --team-lead interview \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id'
}

# -- Tests --

test_state_append_creates_record() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" state append \
    --session "$SESSION_ID" \
    --changed-by orchestrator \
    --state running \
    --description "Workflow started")

  assert_json_field "$OUTPUT" ".session_id" "$SESSION_ID"
  assert_json_field "$OUTPUT" ".changed_by" "orchestrator"
  assert_json_field "$OUTPUT" ".state" "running"
  assert_json_field "$OUTPUT" ".description" "Workflow started"
  assert_json_not_empty "$OUTPUT" ".id" "id"
  assert_json_not_empty "$OUTPUT" ".creation_date" "creation_date"
}

test_state_append_id_is_composite() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" state append \
    --session "$SESSION_ID" \
    --changed-by orchestrator \
    --state pending)

  ID=$(echo "$OUTPUT" | jq -r '.id')
  [[ "$ID" == "${SESSION_ID}:state:"* ]] || {
    echo "expected composite id starting with '${SESSION_ID}:state:', got '${ID}'" >&2
    return 1
  }
}

test_state_current_returns_latest_for_changed_by() {
  SESSION_ID=$(new_session)

  "$ARBITRATOR" state append \
    --session "$SESSION_ID" \
    --changed-by orchestrator \
    --state pending > /dev/null

  "$ARBITRATOR" state append \
    --session "$SESSION_ID" \
    --changed-by orchestrator \
    --state running > /dev/null

  OUTPUT=$("$ARBITRATOR" state current \
    --session "$SESSION_ID" \
    --changed-by orchestrator)

  assert_json_field "$OUTPUT" ".state" "running"
}

test_state_current_returns_latest_after_multiple_appends() {
  SESSION_ID=$(new_session)

  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by worker --state pending > /dev/null
  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by worker --state running > /dev/null
  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by worker --state complete > /dev/null

  OUTPUT=$("$ARBITRATOR" state current \
    --session "$SESSION_ID" \
    --changed-by worker)

  assert_json_field "$OUTPUT" ".state" "complete"
}

test_state_list_returns_all_in_order() {
  SESSION_ID=$(new_session)

  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by orchestrator --state pending > /dev/null
  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by orchestrator --state running > /dev/null
  "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by orchestrator --state complete > /dev/null

  OUTPUT=$("$ARBITRATOR" state list --session "$SESSION_ID")

  assert_json_count "$OUTPUT" "3" "expected 3 state records"

  FIRST_STATE=$(echo "$OUTPUT" | jq -r '.[0].state')
  LAST_STATE=$(echo "$OUTPUT" | jq -r '.[2].state')
  assert_eq "$FIRST_STATE" "pending" "first state"
  assert_eq "$LAST_STATE" "complete" "last state"
}

test_state_list_empty_session() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" state list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "0" "new session should have no state records"
}

test_state_append_missing_flags() {
  SESSION_ID=$(new_session)

  if "$ARBITRATOR" state append --session "$SESSION_ID" --changed-by orchestrator 2>/dev/null; then
    echo "expected failure for missing --state flag" >&2
    return 1
  fi
}

# -- Run --

run_test "state append creates a record with all fields" test_state_append_creates_record
run_test "state append id is a composite id" test_state_append_id_is_composite
run_test "state current returns latest for changed_by" test_state_current_returns_latest_for_changed_by
run_test "state current returns latest after multiple appends" test_state_current_returns_latest_after_multiple_appends
run_test "state list returns all transitions in order" test_state_list_returns_all_in_order
run_test "state list returns empty for new session" test_state_list_empty_session
run_test "state append fails with missing required flags" test_state_append_missing_flags

test_summary
