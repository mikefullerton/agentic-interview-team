#!/bin/bash
# 06-artifacts.sh — Contract tests for artifact resource
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

# -- Tests --

test_artifact_create_returns_id() {
  SESSION_ID=$(make_session)
  OUTPUT=$("$ARBITRATOR" artifact create \
    --session "$SESSION_ID" \
    --artifact "https://example.com/artifact/abc123")
  ARTIFACT_ID=$(echo "$OUTPUT" | jq -r '.artifact_id')
  assert_not_empty "$ARTIFACT_ID" "artifact_id"
}

test_artifact_create_with_message_and_description() {
  SESSION_ID=$(make_session)
  OUTPUT=$("$ARBITRATOR" artifact create \
    --session "$SESSION_ID" \
    --artifact "https://example.com/artifact/def456" \
    --message "Initial build" \
    --description "First pass at the output artifact")
  ARTIFACT_ID=$(echo "$OUTPUT" | jq -r '.artifact_id')
  assert_not_empty "$ARTIFACT_ID" "artifact_id"

  # Verify stored fields by listing and checking the artifact
  LIST=$("$ARBITRATOR" artifact list --session "$SESSION_ID")
  assert_json_field "$LIST" '.[0].message' "Initial build"
  assert_json_field "$LIST" '.[0].description' "First pass at the output artifact"
}

test_artifact_list_returns_all() {
  SESSION_ID=$(make_session)
  "$ARBITRATOR" artifact create --session "$SESSION_ID" --artifact "https://example.com/a1" > /dev/null
  "$ARBITRATOR" artifact create --session "$SESSION_ID" --artifact "https://example.com/a2" > /dev/null
  "$ARBITRATOR" artifact create --session "$SESSION_ID" --artifact "https://example.com/a3" > /dev/null

  OUTPUT=$("$ARBITRATOR" artifact list --session "$SESSION_ID")
  assert_json_count "$OUTPUT" "3" "should have 3 artifacts"
}

test_artifact_link_state_adds_to_array() {
  SESSION_ID=$(make_session)
  ARTIFACT_ID=$("$ARBITRATOR" artifact create \
    --session "$SESSION_ID" \
    --artifact "https://example.com/artifact/xyz" \
    | jq -r '.artifact_id')

  STATE_OUTPUT=$("$ARBITRATOR" state append \
    --session "$SESSION_ID" \
    --state reviewing \
    --changed-by orchestrator)
  STATE_ID=$(echo "$STATE_OUTPUT" | jq -r '.id')

  OUTPUT=$("$ARBITRATOR" artifact link-state \
    --artifact "$ARTIFACT_ID" \
    --state "$STATE_ID")

  COUNT=$(echo "$OUTPUT" | jq '.linked_states | length')
  assert_eq "$COUNT" "1" "linked_states should have 1 entry"
  assert_json_field "$OUTPUT" '.linked_states[0]' "$STATE_ID"
}

# -- Run --

run_test "artifact create returns artifact_id" test_artifact_create_returns_id
run_test "artifact create with message and description" test_artifact_create_with_message_and_description
run_test "artifact list returns all artifacts" test_artifact_list_returns_all
run_test "artifact link-state adds to linked_states" test_artifact_link_state_adds_to_array

test_summary
