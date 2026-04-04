#!/bin/bash
# 07-references.sh — Contract tests for reference resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Setup --

make_result() {
  local session_id="$1"
  local specialist="${2:-security}"
  "$ARBITRATOR" result create \
    --session "$session_id" \
    --specialist "$specialist" \
    | jq -r '.result_id'
}

make_session() {
  "$ARBITRATOR" session create \
    --playbook interview \
    --team-lead interview \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id'
}

# -- Tests --

test_reference_create_returns_id() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID")

  OUTPUT=$("$ARBITRATOR" reference create \
    --result "$RESULT_ID" \
    --path "guidelines/security.md" \
    --type guideline)
  REFERENCE_ID=$(echo "$OUTPUT" | jq -r '.reference_id')
  assert_not_empty "$REFERENCE_ID" "reference_id"
}

test_reference_list_returns_references() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "ux")

  "$ARBITRATOR" reference create \
    --result "$RESULT_ID" \
    --path "guidelines/ux.md" \
    --type guideline > /dev/null
  "$ARBITRATOR" reference create \
    --result "$RESULT_ID" \
    --path "principles/accessibility.md" \
    --type principle > /dev/null

  OUTPUT=$("$ARBITRATOR" reference list --result "$RESULT_ID")
  assert_json_count "$OUTPUT" "2" "should have 2 references"
  assert_json_field "$OUTPUT" '.[0].type' "guideline"
  assert_json_field "$OUTPUT" '.[1].type' "principle"
}

test_reference_list_empty_for_no_references() {
  SESSION_ID=$(make_session)
  RESULT_ID=$(make_result "$SESSION_ID" "architecture")

  OUTPUT=$("$ARBITRATOR" reference list --result "$RESULT_ID")
  assert_json_count "$OUTPUT" "0" "should have 0 references"
}

# -- Run --

run_test "reference create returns reference_id" test_reference_create_returns_id
run_test "reference list returns references for a result" test_reference_list_returns_references
run_test "reference list returns empty for no references" test_reference_list_empty_for_no_references

test_summary
