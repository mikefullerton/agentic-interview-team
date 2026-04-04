#!/bin/bash
# 04-issues.sh — Contract tests for issue resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_issue_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Login broken" \
    --description "Users cannot log in" \
    --severity "high" \
    --status "open")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_issue_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Crash on startup" \
    --description "App crashes immediately on launch" \
    --severity "critical" \
    --status "open" | jq -r '.id')
  OUTPUT=$("$PROJECT_STORAGE" issue get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".title" "Crash on startup"
  assert_json_field "$OUTPUT" ".status" "open"
  assert_json_field "$OUTPUT" ".severity" "critical"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  rm -rf "$DIR"
}

test_issue_list_returns_issues() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "I1" --description "Issue one" --severity "low" --status "open" > /dev/null
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "I2" --description "Issue two" --severity "high" --status "open" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" issue list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should have 2 issues"
  rm -rf "$DIR"
}

test_issue_list_filters_by_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "I1" --description "Open issue" --severity "low" --status "open" > /dev/null
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "I2" --description "Closed issue" --severity "low" --status "closed" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" issue list --project "$DIR" --status "closed")
  assert_json_count "$OUTPUT" "1" "should have 1 closed issue"
  assert_json_field "$OUTPUT" ".[0].status" "closed"
  rm -rf "$DIR"
}

test_issue_list_filters_by_severity() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "Low" --description "Minor problem" --severity "low" --status "open" > /dev/null
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" --title "Critical" --description "Major problem" --severity "critical" --status "open" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" issue list --project "$DIR" --severity "critical")
  assert_json_count "$OUTPUT" "1" "should have 1 critical issue"
  assert_json_field "$OUTPUT" ".[0].severity" "critical"
  rm -rf "$DIR"
}

test_issue_create_with_source() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Sourced issue" \
    --description "Came from monitoring alert" \
    --severity "medium" \
    --status "open" \
    --source "monitoring")
  ID=$(echo "$OUTPUT" | jq -r '.id')
  DETAILS=$("$PROJECT_STORAGE" issue get --project "$DIR" --id "$ID")
  assert_json_field "$DETAILS" ".source" "monitoring"
  rm -rf "$DIR"
}

test_issue_create_fails_missing_flags() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Incomplete" \
    --severity "high" 2>/dev/null; then
    echo "expected failure for missing --description and --status" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "issue create returns id" test_issue_create_returns_id
run_test "issue get returns all fields including description" test_issue_get_returns_all_fields
run_test "issue list returns issues" test_issue_list_returns_issues
run_test "issue list filters by status" test_issue_list_filters_by_status
run_test "issue list filters by severity" test_issue_list_filters_by_severity
run_test "issue create with optional source" test_issue_create_with_source
run_test "issue create fails with missing flags" test_issue_create_fails_missing_flags

test_summary
