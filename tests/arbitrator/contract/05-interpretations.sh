#!/bin/bash
# 05-interpretations.sh — Contract tests for interpretation resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Helper: bootstrap a session + result + finding --

make_finding() {
  local playbook="${1:-interview}"
  SESSION_ID=$("$ARBITRATOR" session create \
    --playbook "$playbook" \
    --team-lead interview \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id')

  RESULT_ID=$("$ARBITRATOR" result create \
    --session "$SESSION_ID" \
    --specialist analysis \
    | jq -r '.result_id')

  FINDING_ID=$("$ARBITRATOR" finding create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist analysis \
    --category design \
    --severity medium \
    --title "Architecture concern" \
    --detail "The current design does not support horizontal scaling" \
    | jq -r '.finding_id')
}

# -- Interpretation tests --

test_interpretation_create_returns_id() {
  make_finding
  OUTPUT=$("$ARBITRATOR" interpretation create \
    --session "$SESSION_ID" \
    --finding "$FINDING_ID" \
    --specialist analysis \
    --interpretation "This concern stems from tight coupling between the data layer and business logic")
  INTERP_ID=$(echo "$OUTPUT" | jq -r '.interpretation_id')
  assert_not_empty "$INTERP_ID" "interpretation_id"
}

test_interpretation_list_returns_for_finding() {
  make_finding
  "$ARBITRATOR" interpretation create \
    --session "$SESSION_ID" \
    --finding "$FINDING_ID" \
    --specialist analysis \
    --interpretation "First interpretation of this finding" > /dev/null

  OUTPUT=$("$ARBITRATOR" interpretation list --finding "$FINDING_ID")
  COUNT=$(echo "$OUTPUT" | jq 'length')
  [[ "$COUNT" -ge 1 ]] || { echo "expected at least 1 interpretation, got ${COUNT}" >&2; return 1; }

  INTERP_TEXT=$(echo "$OUTPUT" | jq -r '.[0].interpretation')
  assert_not_empty "$INTERP_TEXT" "interpretation text"
  assert_json_field "$(echo "$OUTPUT" | jq '.[0]')" ".finding_id" "$FINDING_ID"
}

test_interpretation_list_nonexistent_finding_fails_gracefully() {
  FAKE_FINDING="20260101-000000-0000:finding:security:9999"
  # Should either return empty array or exit non-zero — must not crash with unhandled error
  OUTPUT=$("$ARBITRATOR" interpretation list --finding "$FAKE_FINDING" 2>/dev/null) || true
  # If it returned output, it should be a valid JSON array (possibly empty)
  if [[ -n "$OUTPUT" ]]; then
    echo "$OUTPUT" | jq 'if type == "array" then . else error end' > /dev/null 2>&1 || {
      echo "expected JSON array or graceful failure, got: ${OUTPUT}" >&2
      return 1
    }
  fi
}

# -- Run --

run_test "interpretation create returns id" test_interpretation_create_returns_id
run_test "interpretation list returns interpretations for a finding" test_interpretation_list_returns_for_finding
run_test "interpretation for nonexistent finding fails gracefully" test_interpretation_list_nonexistent_finding_fails_gracefully

test_summary
