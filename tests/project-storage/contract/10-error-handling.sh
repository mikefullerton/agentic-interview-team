#!/bin/bash
# 10-error-handling.sh — Contract tests for error handling
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_unknown_resource_fails() {
  if "$PROJECT_STORAGE" nonexistent list --project "/tmp" 2>/dev/null; then
    echo "expected failure for unknown resource" >&2
    return 1
  fi
}

test_unknown_action_fails() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" todo frobnicate --project "$DIR" 2>/dev/null; then
    echo "expected failure for unknown action" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_get_nonexistent_item_fails() {
  DIR=$(new_project)
  if "$PROJECT_STORAGE" todo get --project "$DIR" --id "todo-9999" 2>/dev/null; then
    echo "expected failure for nonexistent item" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_create_on_nonexistent_project_fails() {
  FAKE_DIR="/tmp/no-such-project-$$"
  if "$PROJECT_STORAGE" todo create \
    --project "$FAKE_DIR" \
    --title "Will fail" \
    --description "Project does not exist" \
    --priority "low" \
    --status "open" 2>/dev/null; then
    echo "expected failure for nonexistent project" >&2
    return 1
  fi
}

test_list_on_nonexistent_project_fails() {
  FAKE_DIR="/tmp/no-such-project-$$"
  if "$PROJECT_STORAGE" todo list --project "$FAKE_DIR" 2>/dev/null; then
    echo "expected failure for nonexistent project" >&2
    return 1
  fi
}

run_test "unknown resource fails" test_unknown_resource_fails
run_test "unknown action fails" test_unknown_action_fails
run_test "get nonexistent item fails" test_get_nonexistent_item_fails
run_test "create on nonexistent project fails" test_create_on_nonexistent_project_fails
run_test "list on nonexistent project fails" test_list_on_nonexistent_project_fails

test_summary
