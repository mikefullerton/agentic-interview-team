#!/bin/bash
# 08-retries.sh — Contract tests for retry resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Setup --

make_session() {
  "$ARBITRATOR" session create \
    --playbook interview \
    --team-lead interview \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id'
}

make_state() {
  local session_id="$1"
  "$ARBITRATOR" state append \
    --session "$session_id" \
    --state reviewing \
    --changed-by orchestrator \
    | jq -r '.id'
}

# -- Tests --

test_retry_create_returns_id() {
  SESSION_ID=$(make_session)
  STATE_ID=$(make_state "$SESSION_ID")

  OUTPUT=$("$ARBITRATOR" retry create \
    --session "$SESSION_ID" \
    --state "$STATE_ID" \
    --reason "Specialist output was incomplete")
  RETRY_ID=$(echo "$OUTPUT" | jq -r '.retry_id')
  assert_not_empty "$RETRY_ID" "retry_id"
}

test_retry_create_stores_reason_and_state_link() {
  SESSION_ID=$(make_session)
  STATE_ID=$(make_state "$SESSION_ID")

  "$ARBITRATOR" retry create \
    --session "$SESSION_ID" \
    --state "$STATE_ID" \
    --reason "Validation threshold not met" > /dev/null

  OUTPUT=$("$ARBITRATOR" retry list --session "$SESSION_ID")
  assert_json_field "$OUTPUT" '.[0].reason' "Validation threshold not met"
  assert_json_field "$OUTPUT" '.[0].session_state_id' "$STATE_ID"
  assert_json_field "$OUTPUT" '.[0].session_id' "$SESSION_ID"
}

test_retry_list_returns_all() {
  SESSION_ID=$(make_session)
  STATE_ID=$(make_state "$SESSION_ID")

  "$ARBITRATOR" retry create --session "$SESSION_ID" --state "$STATE_ID" --reason "First retry" > /dev/null
  "$ARBITRATOR" retry create --session "$SESSION_ID" --state "$STATE_ID" --reason "Second retry" > /dev/null

  OUTPUT=$("$ARBITRATOR" retry list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "2" "should have 2 retries"
}

# -- Run --

run_test "retry create returns retry_id" test_retry_create_returns_id
run_test "retry create stores reason and state link" test_retry_create_stores_reason_and_state_link
run_test "retry list returns all retries" test_retry_list_returns_all

test_summary
