#!/bin/bash
# 09-filtering.sh — Contract tests for cross-type filtering
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_todo_list_with_multiple_filters() {
  DIR=$(new_project)
  # Create todos with different combinations of status + priority
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "High open todo" \
    --description "Should match" \
    --priority "high" \
    --status "open" > /dev/null
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Low open todo" \
    --description "Should not match" \
    --priority "low" \
    --status "open" > /dev/null
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "High done todo" \
    --description "Should not match" \
    --priority "high" \
    --status "done" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" todo list --project "$DIR" --status "open" --priority "high")
  assert_json_count "$OUTPUT" "1" "should return only 1 todo matching both filters"
  assert_json_field "$OUTPUT" ".[0].title" "High open todo"
  rm -rf "$DIR"
}

test_todo_list_returns_empty_when_no_matches() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Some todo" \
    --description "Exists but won't match" \
    --priority "low" \
    --status "open" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" todo list --project "$DIR" --status "done")
  assert_json_count "$OUTPUT" "0" "should return empty array when no matches"
  rm -rf "$DIR"
}

test_issue_list_returns_only_matching_severity() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Critical bug" \
    --description "App crashes on login" \
    --severity "critical" \
    --status "open" > /dev/null
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Minor UI glitch" \
    --description "Button misaligned" \
    --severity "low" \
    --status "open" > /dev/null
  "$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Another critical" \
    --description "Data corruption possible" \
    --severity "critical" \
    --status "open" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" issue list --project "$DIR" --severity "critical")
  assert_json_count "$OUTPUT" "2" "should return 2 critical issues"
  rm -rf "$DIR"
}

test_milestone_list_returns_only_matching_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Alpha" \
    --description "Alpha release" \
    --status "completed" > /dev/null
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Beta" \
    --description "Beta release" \
    --status "planned" > /dev/null
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "GA" \
    --description "General availability" \
    --status "planned" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" milestone list --project "$DIR" --status "planned")
  assert_json_count "$OUTPUT" "2" "should return 2 planned milestones"
  rm -rf "$DIR"
}

run_test "todo list with multiple filters (status + priority)" test_todo_list_with_multiple_filters
run_test "todo list returns empty when no matches" test_todo_list_returns_empty_when_no_matches
run_test "issue list returns only matching severity" test_issue_list_returns_only_matching_severity
run_test "milestone list returns only matching status" test_milestone_list_returns_only_matching_status

test_summary
