#!/bin/bash
# 08-updates-and-deletes.sh — Contract tests for update and delete operations
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_todo_update_changes_status() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Write tests" \
    --description "Add contract tests" \
    --priority "high" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" todo update --project "$DIR" --id "$ID" --status "done" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".status" "done"
  rm -rf "$DIR"
}

test_todo_update_changes_priority() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Refactor auth" \
    --description "Clean up auth module" \
    --priority "low" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" todo update --project "$DIR" --id "$ID" --priority "high" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".priority" "high"
  rm -rf "$DIR"
}

test_milestone_update_changes_target_date() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" milestone create \
    --project "$DIR" \
    --name "Beta Release" \
    --description "Public beta launch" \
    --status "planned" \
    --target-date "2024-06-01" | jq -r '.id')

  "$PROJECT_STORAGE" milestone update --project "$DIR" --id "$ID" --target-date "2024-07-15" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" milestone get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".target_date" "2024-07-15"
  rm -rf "$DIR"
}

test_issue_update_changes_severity() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Login timeout" \
    --description "Users get logged out too quickly" \
    --severity "low" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" issue update --project "$DIR" --id "$ID" --severity "high" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" issue get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".severity" "high"
  rm -rf "$DIR"
}

test_concern_update_changes_status() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" concern create \
    --project "$DIR" \
    --title "Performance at scale" \
    --description "May not handle 10k concurrent users" \
    --raised-by "alice" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" concern update --project "$DIR" --id "$ID" --status "resolved" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" concern get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".status" "resolved"
  rm -rf "$DIR"
}

test_todo_delete_removes_item() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Todo to delete" \
    --description "This will be deleted" \
    --priority "low" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" todo delete --project "$DIR" --id "$ID" > /dev/null

  if "$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID" 2>/dev/null; then
    echo "expected get to fail after delete" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_issue_delete_removes_item() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" issue create \
    --project "$DIR" \
    --title "Issue to delete" \
    --description "This will be deleted" \
    --severity "low" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" issue delete --project "$DIR" --id "$ID" > /dev/null

  if "$PROJECT_STORAGE" issue get --project "$DIR" --id "$ID" 2>/dev/null; then
    echo "expected get to fail after delete" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_delete_nonexistent_item_fails() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" todo delete --project "$DIR" --id "todo-9999" 2>/dev/null; then
    echo "expected failure for nonexistent item" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_update_sets_modified_date() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" todo create \
    --project "$DIR" \
    --title "Dated todo" \
    --description "Check modified date" \
    --priority "low" \
    --status "open" | jq -r '.id')

  "$PROJECT_STORAGE" todo update --project "$DIR" --id "$ID" --status "in-progress" > /dev/null
  OUTPUT=$("$PROJECT_STORAGE" todo get --project "$DIR" --id "$ID")
  assert_json_not_empty "$OUTPUT" ".modified" "modified date should be set after update"
  rm -rf "$DIR"
}

run_test "todo update changes status" test_todo_update_changes_status
run_test "todo update changes priority" test_todo_update_changes_priority
run_test "milestone update changes target-date" test_milestone_update_changes_target_date
run_test "issue update changes severity" test_issue_update_changes_severity
run_test "concern update changes status" test_concern_update_changes_status
run_test "todo delete removes item" test_todo_delete_removes_item
run_test "issue delete removes item" test_issue_delete_removes_item
run_test "delete nonexistent item fails" test_delete_nonexistent_item_fails
run_test "update sets modified date" test_update_sets_modified_date

test_summary
