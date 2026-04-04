#!/bin/bash
# 05-concerns.sh — Contract tests for concern resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_concern_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" concern create \
    --project "$DIR" \
    --title "Scalability risk" \
    --description "System may not handle peak load" \
    --raised-by "alice" \
    --status "open")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_concern_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" concern create \
    --project "$DIR" \
    --title "Data retention policy" \
    --description "No policy defined for user data retention" \
    --raised-by "bob" \
    --status "open" | jq -r '.id')
  OUTPUT=$("$PROJECT_STORAGE" concern get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".title" "Data retention policy"
  assert_json_field "$OUTPUT" ".status" "open"
  assert_json_field "$OUTPUT" ".raised_by" "bob"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  rm -rf "$DIR"
}

test_concern_list_returns_concerns() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" concern create \
    --project "$DIR" --title "C1" --description "Concern one" --raised-by "alice" --status "open" > /dev/null
  "$PROJECT_STORAGE" concern create \
    --project "$DIR" --title "C2" --description "Concern two" --raised-by "bob" --status "open" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" concern list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should have 2 concerns"
  rm -rf "$DIR"
}

test_concern_list_filters_by_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" concern create \
    --project "$DIR" --title "C1" --description "Open concern" --raised-by "alice" --status "open" > /dev/null
  "$PROJECT_STORAGE" concern create \
    --project "$DIR" --title "C2" --description "Resolved concern" --raised-by "bob" --status "resolved" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" concern list --project "$DIR" --status "resolved")
  assert_json_count "$OUTPUT" "1" "should have 1 resolved concern"
  assert_json_field "$OUTPUT" ".[0].status" "resolved"
  rm -rf "$DIR"
}

test_concern_create_with_related_to() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" concern create \
    --project "$DIR" \
    --title "Related concern" \
    --description "Links to an existing issue" \
    --raised-by "carol" \
    --status "open" \
    --related-to "issue-0001")
  ID=$(echo "$OUTPUT" | jq -r '.id')
  DETAILS=$("$PROJECT_STORAGE" concern get --project "$DIR" --id "$ID")
  assert_json_field "$DETAILS" ".related_to" "issue-0001"
  rm -rf "$DIR"
}

test_concern_create_fails_missing_flags() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" concern create \
    --project "$DIR" \
    --title "Incomplete" \
    --raised-by "alice" 2>/dev/null; then
    echo "expected failure for missing --description and --status" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "concern create returns id" test_concern_create_returns_id
run_test "concern get returns all fields including description" test_concern_get_returns_all_fields
run_test "concern list returns concerns" test_concern_list_returns_concerns
run_test "concern list filters by status" test_concern_list_filters_by_status
run_test "concern create with optional related-to" test_concern_create_with_related_to
run_test "concern create fails with missing flags" test_concern_create_fails_missing_flags

test_summary
