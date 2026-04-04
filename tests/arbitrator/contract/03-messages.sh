#!/bin/bash
# 03-messages.sh — Contract tests for message and gate-option resources
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

test_message_send_creates_record() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type finding \
    --changed-by analyst \
    --content "Initial analysis complete")

  assert_json_field "$OUTPUT" ".session_id" "$SESSION_ID"
  assert_json_field "$OUTPUT" ".type" "finding"
  assert_json_field "$OUTPUT" ".changed_by" "analyst"
  assert_json_field "$OUTPUT" ".content" "Initial analysis complete"
  assert_json_not_empty "$OUTPUT" ".id" "id"
  assert_json_not_empty "$OUTPUT" ".creation_date" "creation_date"
}

test_message_send_id_is_composite() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type finding \
    --changed-by analyst \
    --content "Test message")

  ID=$(echo "$OUTPUT" | jq -r '.id')
  [[ "$ID" == "${SESSION_ID}:message:"* ]] || {
    echo "expected composite id starting with '${SESSION_ID}:message:', got '${ID}'" >&2
    return 1
  }
}

test_message_send_with_optional_fields() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type finding \
    --changed-by security-specialist \
    --content "SQL injection risk detected" \
    --specialist security \
    --category vulnerability \
    --severity high)

  assert_json_field "$OUTPUT" ".specialist" "security"
  assert_json_field "$OUTPUT" ".category" "vulnerability"
  assert_json_field "$OUTPUT" ".severity" "high"
}

test_message_list_returns_all() {
  SESSION_ID=$(new_session)

  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type finding --changed-by analyst --content "First" > /dev/null
  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type gate --changed-by orchestrator --content "Gate check" > /dev/null
  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type finding --changed-by analyst --content "Third" > /dev/null

  OUTPUT=$("$ARBITRATOR" message list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "3" "expected 3 messages"
}

test_message_list_filters_by_type() {
  SESSION_ID=$(new_session)

  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type finding --changed-by analyst --content "Finding 1" > /dev/null
  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type gate --changed-by orchestrator --content "Gate 1" > /dev/null
  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type finding --changed-by analyst --content "Finding 2" > /dev/null

  OUTPUT=$("$ARBITRATOR" message list --session "$SESSION_ID" --type finding)
  assert_json_count "$OUTPUT" "2" "expected 2 finding messages"

  OUTPUT=$("$ARBITRATOR" message list --session "$SESSION_ID" --type gate)
  assert_json_count "$OUTPUT" "1" "expected 1 gate message"
}

test_message_get_retrieves_by_id() {
  SESSION_ID=$(new_session)

  SENT=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type finding \
    --changed-by analyst \
    --content "Findable message")

  MSG_ID=$(echo "$SENT" | jq -r '.id')

  OUTPUT=$("$ARBITRATOR" message get --message "$MSG_ID")
  assert_json_field "$OUTPUT" ".id" "$MSG_ID"
  assert_json_field "$OUTPUT" ".content" "Findable message"
}

test_gate_option_add_creates_option() {
  SESSION_ID=$(new_session)

  MSG=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type gate \
    --changed-by orchestrator \
    --content "Choose an option")

  MSG_ID=$(echo "$MSG" | jq -r '.id')

  OUTPUT=$("$ARBITRATOR" gate-option add \
    --message "$MSG_ID" \
    --option-text "Continue" \
    --is-default 1 \
    --sort-order 1)

  assert_json_field "$OUTPUT" ".message_id" "$MSG_ID"
  assert_json_field "$OUTPUT" ".option_text" "Continue"
  assert_json_field "$OUTPUT" ".is_default" "1"
  assert_json_field "$OUTPUT" ".sort_order" "1"
  assert_json_not_empty "$OUTPUT" ".id" "id"
}

test_gate_option_add_multiple_options() {
  SESSION_ID=$(new_session)

  MSG=$("$ARBITRATOR" message send \
    --session "$SESSION_ID" \
    --type gate \
    --changed-by orchestrator \
    --content "Multi-option gate")

  MSG_ID=$(echo "$MSG" | jq -r '.id')

  OPT1=$("$ARBITRATOR" gate-option add \
    --message "$MSG_ID" --option-text "Yes" --is-default 1 --sort-order 1)
  OPT2=$("$ARBITRATOR" gate-option add \
    --message "$MSG_ID" --option-text "No" --is-default 0 --sort-order 2)

  # Verify both options were created with distinct IDs
  ID1=$(echo "$OPT1" | jq -r '.id')
  ID2=$(echo "$OPT2" | jq -r '.id')
  assert_not_empty "$ID1" "first option id"
  assert_not_empty "$ID2" "second option id"
  [[ "$ID1" != "$ID2" ]] || {
    echo "expected distinct option IDs, got same: ${ID1}" >&2
    return 1
  }
}

test_message_send_missing_flags() {
  SESSION_ID=$(new_session)

  if "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type finding --changed-by analyst 2>/dev/null; then
    echo "expected failure for missing --content flag" >&2
    return 1
  fi
}

test_message_list_empty_session() {
  SESSION_ID=$(new_session)

  OUTPUT=$("$ARBITRATOR" message list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "0" "new session should have no messages"
}

# -- Run --

run_test "message send creates a record" test_message_send_creates_record
run_test "message send id is a composite id" test_message_send_id_is_composite
run_test "message send with optional fields" test_message_send_with_optional_fields
run_test "message list returns all messages" test_message_list_returns_all
run_test "message list filters by type" test_message_list_filters_by_type
run_test "message get retrieves by ID" test_message_get_retrieves_by_id
run_test "gate-option add creates an option linked to a message" test_gate_option_add_creates_option
run_test "gate-option add supports multiple options per message" test_gate_option_add_multiple_options
run_test "message send fails with missing required flags" test_message_send_missing_flags
run_test "message list returns empty for new session" test_message_list_empty_session

test_summary
