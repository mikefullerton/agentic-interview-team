#!/bin/bash
# 04-results-and-findings.sh — Contract tests for result and finding resources
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Helper: create a session for tests --

make_session() {
  "$ARBITRATOR" session create \
    --playbook interview \
    --team-lead interview \
    --user testuser \
    --machine testhost \
    | jq -r '.session_id'
}

# -- Result tests --

test_result_create_returns_id() {
  SESSION_ID=$(make_session)
  OUTPUT=$("$ARBITRATOR" result create \
    --session "$SESSION_ID" \
    --specialist security)
  RESULT_ID=$(echo "$OUTPUT" | jq -r '.result_id')
  assert_not_empty "$RESULT_ID" "result_id"
}

test_result_get_returns_all_fields() {
  SESSION_ID=$(make_session)
  OUTPUT=$("$ARBITRATOR" result create \
    --session "$SESSION_ID" \
    --specialist performance)
  RESULT_ID=$(echo "$OUTPUT" | jq -r '.result_id')

  OUTPUT=$("$ARBITRATOR" result get --result "$RESULT_ID")
  assert_json_field "$OUTPUT" ".specialist" "performance"
  assert_json_field "$OUTPUT" ".session_id" "$SESSION_ID"
  assert_json_field "$OUTPUT" ".result_id" "$RESULT_ID"
  assert_json_not_empty "$OUTPUT" ".creation_date" "creation_date"
}

test_result_list_returns_for_session() {
  SESSION_ID=$(make_session)
  "$ARBITRATOR" result create --session "$SESSION_ID" --specialist security > /dev/null
  "$ARBITRATOR" result create --session "$SESSION_ID" --specialist accessibility > /dev/null

  OUTPUT=$("$ARBITRATOR" result list --session "$SESSION_ID")
  COUNT=$(echo "$OUTPUT" | jq 'length')
  [[ "$COUNT" -ge 2 ]] || { echo "expected at least 2 results, got ${COUNT}" >&2; return 1; }
}

test_result_list_filters_by_specialist() {
  SESSION_ID=$(make_session)
  "$ARBITRATOR" result create --session "$SESSION_ID" --specialist security > /dev/null
  "$ARBITRATOR" result create --session "$SESSION_ID" --specialist performance > /dev/null

  OUTPUT=$("$ARBITRATOR" result list --session "$SESSION_ID" --specialist security)
  assert_json_count "$OUTPUT" "1" "should return exactly 1 security result"
  assert_json_field "$OUTPUT" ".[0].specialist" "security"
}

# -- Finding tests --

test_finding_create_returns_id() {
  SESSION_ID=$(make_session)
  RESULT_ID=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  OUTPUT=$("$ARBITRATOR" finding create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --category vulnerability \
    --severity high \
    --title "SQL injection risk" \
    --detail "User input is not sanitized before query execution")
  FINDING_ID=$(echo "$OUTPUT" | jq -r '.finding_id')
  assert_not_empty "$FINDING_ID" "finding_id"
}

test_finding_get_returns_all_fields() {
  SESSION_ID=$(make_session)
  RESULT_ID=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  OUTPUT=$("$ARBITRATOR" finding create \
    --session "$SESSION_ID" \
    --result "$RESULT_ID" \
    --specialist security \
    --category vulnerability \
    --severity critical \
    --title "Hardcoded credentials" \
    --detail "API key found in source code")
  FINDING_ID=$(echo "$OUTPUT" | jq -r '.finding_id')

  OUTPUT=$("$ARBITRATOR" finding get --finding "$FINDING_ID")
  assert_json_field "$OUTPUT" ".specialist" "security"
  assert_json_field "$OUTPUT" ".session_id" "$SESSION_ID"
  assert_json_field "$OUTPUT" ".result_id" "$RESULT_ID"
  assert_json_field "$OUTPUT" ".category" "vulnerability"
  assert_json_field "$OUTPUT" ".severity" "critical"
  assert_json_field "$OUTPUT" ".title" "Hardcoded credentials"
  assert_json_field "$OUTPUT" ".detail" "API key found in source code"
  assert_json_not_empty "$OUTPUT" ".creation_date" "creation_date"
  assert_json_field "$OUTPUT" ".linked_artifacts" "[]"
}

test_finding_list_returns_findings() {
  SESSION_ID=$(make_session)
  RESULT_ID=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category vuln --severity high --title "Issue one" --detail "Detail one" > /dev/null
  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category vuln --severity low --title "Issue two" --detail "Detail two" > /dev/null

  OUTPUT=$("$ARBITRATOR" finding list --session "$SESSION_ID")
  COUNT=$(echo "$OUTPUT" | jq 'length')
  [[ "$COUNT" -ge 2 ]] || { echo "expected at least 2 findings, got ${COUNT}" >&2; return 1; }
}

test_finding_list_filters_by_specialist() {
  SESSION_ID=$(make_session)
  SEC_RESULT=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')
  PERF_RESULT=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist performance | jq -r '.result_id')

  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$SEC_RESULT" --specialist security \
    --category vuln --severity high --title "Security issue" --detail "Details" > /dev/null
  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$PERF_RESULT" --specialist performance \
    --category perf --severity low --title "Perf issue" --detail "Details" > /dev/null

  OUTPUT=$("$ARBITRATOR" finding list --session "$SESSION_ID" --specialist security)
  for row in $(echo "$OUTPUT" | jq -r '.[].specialist'); do
    [[ "$row" == "security" ]] || { echo "unexpected specialist in filtered list: ${row}" >&2; return 1; }
  done
  COUNT=$(echo "$OUTPUT" | jq 'length')
  [[ "$COUNT" -ge 1 ]] || { echo "expected at least 1 security finding, got ${COUNT}" >&2; return 1; }
}

test_finding_list_filters_by_severity() {
  SESSION_ID=$(make_session)
  RESULT_ID=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category vuln --severity critical --title "Critical issue" --detail "Details" > /dev/null
  "$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category vuln --severity low --title "Low issue" --detail "Details" > /dev/null

  OUTPUT=$("$ARBITRATOR" finding list --session "$SESSION_ID" --severity critical)
  for row in $(echo "$OUTPUT" | jq -r '.[].severity'); do
    [[ "$row" == "critical" ]] || { echo "unexpected severity in filtered list: ${row}" >&2; return 1; }
  done
  COUNT=$(echo "$OUTPUT" | jq 'length')
  [[ "$COUNT" -ge 1 ]] || { echo "expected at least 1 critical finding, got ${COUNT}" >&2; return 1; }
}

test_finding_link_artifact_adds_to_array() {
  SESSION_ID=$(make_session)
  RESULT_ID=$("$ARBITRATOR" result create --session "$SESSION_ID" --specialist security | jq -r '.result_id')

  FINDING_ID=$("$ARBITRATOR" finding create \
    --session "$SESSION_ID" --result "$RESULT_ID" --specialist security \
    --category vuln --severity high --title "Link test" --detail "Details" \
    | jq -r '.finding_id')

  "$ARBITRATOR" finding link-artifact \
    --finding "$FINDING_ID" \
    --artifact "artifact-abc-123" > /dev/null

  OUTPUT=$("$ARBITRATOR" finding get --finding "$FINDING_ID")
  ARTIFACT_COUNT=$(echo "$OUTPUT" | jq '.linked_artifacts | length')
  assert_eq "$ARTIFACT_COUNT" "1" "linked_artifacts should have 1 entry"
  ARTIFACT_VAL=$(echo "$OUTPUT" | jq -r '.linked_artifacts[0]')
  assert_eq "$ARTIFACT_VAL" "artifact-abc-123" "linked artifact id"
}

# -- Run --

run_test "result create returns result_id" test_result_create_returns_id
run_test "result get returns all fields" test_result_get_returns_all_fields
run_test "result list returns results for session" test_result_list_returns_for_session
run_test "result list filters by specialist" test_result_list_filters_by_specialist
run_test "finding create returns finding_id" test_finding_create_returns_id
run_test "finding get returns all fields" test_finding_get_returns_all_fields
run_test "finding list returns findings" test_finding_list_returns_findings
run_test "finding list filters by specialist" test_finding_list_filters_by_specialist
run_test "finding list filters by severity" test_finding_list_filters_by_severity
run_test "finding link-artifact adds to linked_artifacts" test_finding_link_artifact_adds_to_array

test_summary
