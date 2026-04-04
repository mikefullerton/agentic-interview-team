#!/bin/bash
# 03-todos.sh — Contract tests for todo resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_todo_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Write tests" \
    --description "Cover all edge cases" \
    --priority "high" \
    --status "open")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_todo_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Fix bug" \
    --description "Detailed bug description" \
    --priority "medium" \
    --status "open" | jq -r '.id')
  OUTPUT=$("$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".title" "Fix bug"
  assert_json_field "$OUTPUT" ".status" "open"
  assert_json_field "$OUTPUT" ".priority" "medium"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  rm -rf "$DIR"
}

test_todo_list_returns_todos() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "T1" --description "Task one" --priority "high" --status "open" > /dev/null
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "T2" --description "Task two" --priority "low" --status "open" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should have 2 todos"
  rm -rf "$DIR"
}

test_todo_list_filters_by_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "T1" --description "Open task" --priority "high" --status "open" > /dev/null
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "T2" --description "Done task" --priority "low" --status "done" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo list --project "$DIR" --status "open")
  assert_json_count "$OUTPUT" "1" "should have 1 open todo"
  assert_json_field "$OUTPUT" ".[0].status" "open"
  rm -rf "$DIR"
}

test_todo_list_filters_by_priority() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "High P" --description "Urgent" --priority "high" --status "open" > /dev/null
  "$PROJECT_STORAGE" todo create \
    --project "$DIR" --title "Low P" --description "Not urgent" --priority "low" --status "open" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo list --project "$DIR" --priority "high")
  assert_json_count "$OUTPUT" "1" "should have 1 high priority todo"
  assert_json_field "$OUTPUT" ".[0].priority" "high"
  rm -rf "$DIR"
}

test_todo_create_with_assignee_and_milestone() {
  DIR=$(new_project)
  MILESTONE_ID=$("$PROJECT_STORAGE" milestone create \
    --project "$DIR" --name "Sprint 1" --description "First sprint" --status "pending" | jq -r '.id')
  OUTPUT=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Assigned task" \
    --description "Task with assignee and milestone" \
    --priority "medium" \
    --status "open" \
    --assignee "alice" \
    --milestone "$MILESTONE_ID")
  ID=$(echo "$OUTPUT" | jq -r '.id')
  DETAILS=$("$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID")
  assert_json_field "$DETAILS" ".assignee" "alice"
  assert_json_field "$DETAILS" ".milestone" "$MILESTONE_ID"
  rm -rf "$DIR"
}

test_todo_create_fails_missing_flags() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Incomplete" \
    --priority "high" 2>/dev/null; then
    echo "expected failure for missing --description and --status" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "todo create returns id" test_todo_create_returns_id
run_test "todo get returns all fields including description" test_todo_get_returns_all_fields
run_test "todo list returns todos" test_todo_list_returns_todos
run_test "todo list filters by status" test_todo_list_filters_by_status
run_test "todo list filters by priority" test_todo_list_filters_by_priority
run_test "todo create with optional assignee and milestone" test_todo_create_with_assignee_and_milestone
run_test "todo create fails with missing flags" test_todo_create_fails_missing_flags

test_summary
