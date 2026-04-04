#!/bin/bash
# 09-reports.sh — Contract tests for report queries (progressive disclosure)
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Helper: set up a populated session --

setup_populated_session() {
  SESSION_ID=$("$ARBITRATOR" session create \
    --playbook generate \
    --team-lead analysis \
    --user testuser \
    --machine testhost | jq -r '.session_id')

  # State transitions
  "$ARBITRATOR" state append \
    --session "$SESSION_ID" --changed-by team-lead:analysis --state running --description "Starting" > /dev/null
  "$ARBITRATOR" state append \
    --session "$SESSION_ID" --changed-by specialist:security --state running --description "Analyzing" > /dev/null

  # Result + findings
  RESULT_ID=$("$ARBITRATOR" result create \
    --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  FINDING_ID=$("$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category gap --severity critical --title "No CSRF" --detail "Missing CSRF tokens" | jq -r '.finding_id')

  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category recommendation --severity minor --title "Add rate limiting" --detail "API has no rate limits" > /dev/null

  # Interpretation
  "$ARBITRATOR" interpretation create \
    --session "$SESSION_ID" --finding "$FINDING_ID" --specialist security \
    --interpretation "Your forms are vulnerable to cross-site request forgery" > /dev/null

  # Artifact linked to finding
  ARTIFACT_ID=$("$ARBITRATOR" artifact create \
    --session "$SESSION_ID" --artifact "guidelines/security/csrf.md" \
    --message "CSRF guideline requires token validation" | jq -r '.artifact_id')
  "$ARBITRATOR" finding link-artifact --finding "$FINDING_ID" --artifact "$ARTIFACT_ID" > /dev/null

  # Reference
  "$ARBITRATOR" session add-path --session "$SESSION_ID" --path "guidelines/security/auth.md" --type guideline > /dev/null
  "$ARBITRATOR" reference create --result "$RESULT_ID" --path "guidelines/security/auth.md" --type guideline > /dev/null

  # Message
  "$ARBITRATOR" message send \
    --session "$SESSION_ID" --type notification --changed-by team-lead:analysis \
    --content "Security analysis complete" --specialist security --severity info --category result > /dev/null

  # Retry
  STATE_ID=$("$ARBITRATOR" state append \
    --session "$SESSION_ID" --changed-by specialist:security --state failed --description "Verifier rejected" | jq -r '.id')
  "$ARBITRATOR" retry create --session "$SESSION_ID" --state "$STATE_ID" --reason "Missing auth checks" > /dev/null

  echo "$SESSION_ID:$FINDING_ID"
}

# -- Tests --

test_report_overview() {
  IDS=$(setup_populated_session)
  SESSION_ID="${IDS%%:*}"

  OUTPUT=$("$ARBITRATOR" report overview --session "$SESSION_ID")

  # Has session metadata
  assert_json_field "$OUTPUT" ".session.playbook" "generate"

  # Has current state
  assert_json_not_empty "$OUTPUT" ".current_state.state" "current state"

  # Has specialist summary
  SPEC_COUNT=$(echo "$OUTPUT" | jq '.specialists | length')
  [[ "$SPEC_COUNT" -ge 1 ]] || { echo "expected at least 1 specialist, got ${SPEC_COUNT}" >&2; return 1; }

  SECURITY=$(echo "$OUTPUT" | jq '.specialists[] | select(.specialist == "security")')
  FINDINGS_COUNT=$(echo "$SECURITY" | jq '.findings_count')
  assert_eq "$FINDINGS_COUNT" "2" "security findings count"
}

test_report_specialist() {
  IDS=$(setup_populated_session)
  SESSION_ID="${IDS%%:*}"

  OUTPUT=$("$ARBITRATOR" report specialist --session "$SESSION_ID" --specialist security)

  # Has result
  assert_json_field "$OUTPUT" ".result.specialist" "security"

  # Has findings
  FINDING_COUNT=$(echo "$OUTPUT" | jq '.findings | length')
  assert_eq "$FINDING_COUNT" "2" "findings count"

  # Has interpretations
  INTERP_COUNT=$(echo "$OUTPUT" | jq '.interpretations | length')
  assert_eq "$INTERP_COUNT" "1" "interpretations count"

  # Has references
  REF_COUNT=$(echo "$OUTPUT" | jq '.references | length')
  assert_eq "$REF_COUNT" "1" "references count"
}

test_report_finding() {
  IDS=$(setup_populated_session)
  FINDING_ID="${IDS#*:}"

  OUTPUT=$("$ARBITRATOR" report finding --finding "$FINDING_ID")

  # Has finding detail
  assert_json_field "$OUTPUT" ".finding.title" "No CSRF"
  assert_json_field "$OUTPUT" ".finding.severity" "critical"

  # Has interpretation
  assert_json_not_empty "$OUTPUT" ".interpretation.interpretation" "interpretation"

  # Has linked artifacts
  ARTIFACT_COUNT=$(echo "$OUTPUT" | jq '.linked_artifacts | length')
  assert_eq "$ARTIFACT_COUNT" "1" "linked artifact count"
}

test_report_trace() {
  IDS=$(setup_populated_session)
  SESSION_ID="${IDS%%:*}"

  OUTPUT=$("$ARBITRATOR" report trace --session "$SESSION_ID")

  # Has state transitions
  STATE_COUNT=$(echo "$OUTPUT" | jq '.states | length')
  [[ "$STATE_COUNT" -ge 3 ]] || { echo "expected at least 3 states, got ${STATE_COUNT}" >&2; return 1; }

  # Has retries
  RETRY_COUNT=$(echo "$OUTPUT" | jq '.retries | length')
  assert_eq "$RETRY_COUNT" "1" "retry count"

  # Has messages
  MSG_COUNT=$(echo "$OUTPUT" | jq '.messages | length')
  assert_eq "$MSG_COUNT" "1" "message count"
}

test_report_specialist_nonexistent() {
  IDS=$(setup_populated_session)
  SESSION_ID="${IDS%%:*}"

  if "$ARBITRATOR" report specialist --session "$SESSION_ID" --specialist nonexistent 2>/dev/null; then
    echo "expected failure for nonexistent specialist" >&2
    return 1
  fi
}

# -- Run --

run_test "report overview returns session + state + specialists" test_report_overview
run_test "report specialist returns result + findings + interpretations + references" test_report_specialist
run_test "report finding returns detail + interpretation + linked artifacts" test_report_finding
run_test "report trace returns states + retries + messages" test_report_trace
run_test "report specialist fails for nonexistent specialist" test_report_specialist_nonexistent

test_summary
