#!/bin/bash
# 02-milestones.sh — Contract tests for milestone resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_milestone_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Launch v1" \
    --description "First release" \
    --status "pending")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_milestone_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Phase One" \
    --description "Complete phase one work" \
    --status "pending" | jq -r '.id')
  OUTPUT=$("$PROJECT_STORAGE" milestone get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".name" "Phase One"
  assert_json_field "$OUTPUT" ".status" "pending"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  rm -rf "$DIR"
}

test_milestone_list_returns_milestones() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" --name "M1" --description "Milestone one" --status "pending" > /dev/null
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" --name "M2" --description "Milestone two" --status "in-progress" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" milestone list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should have 2 milestones"
  rm -rf "$DIR"
}

test_milestone_list_filters_by_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" --name "M1" --description "First" --status "pending" > /dev/null
  "$PROJECT_STORAGE" milestone create \
    --project "$DIR" --name "M2" --description "Second" --status "done" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" milestone list --project "$DIR" --status "done")
  assert_json_count "$OUTPUT" "1" "should have 1 done milestone"
  assert_json_field "$OUTPUT" ".[0].status" "done"
  rm -rf "$DIR"
}

test_milestone_create_with_target_date() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Dated Milestone" \
    --description "Has a target date" \
    --status "pending" \
    --target-date "2026-06-01")
  ID=$(echo "$OUTPUT" | jq -r '.id')
  DETAILS=$("$PROJECT_STORAGE" milestone get --project "$DIR" --id "$ID")
  assert_json_field "$DETAILS" ".target_date" "2026-06-01"
  rm -rf "$DIR"
}

test_milestone_create_fails_missing_flags() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Incomplete" \
    --status "pending" 2>/dev/null; then
    echo "expected failure for missing --description" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "milestone create returns id" test_milestone_create_returns_id
run_test "milestone get returns all fields including description" test_milestone_get_returns_all_fields
run_test "milestone list returns milestones" test_milestone_list_returns_milestones
run_test "milestone list filters by status" test_milestone_list_filters_by_status
run_test "milestone create with optional target-date" test_milestone_create_with_target_date
run_test "milestone create fails with missing flags" test_milestone_create_fails_missing_flags

test_summary
