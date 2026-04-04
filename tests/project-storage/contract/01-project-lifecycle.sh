#!/bin/bash
# 01-project-lifecycle.sh — Contract tests for project resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_project_init() {
  DIR=$(mktemp -d)
  OUTPUT=$("$PROJECT_STORAGE" project init --name "my-project" --description "Test" --path "$DIR")
  assert_json_field "$OUTPUT" ".name" "my-project"
  [[ -f "$DIR/.dev-team-project/manifest.json" ]] || { echo "manifest.json missing" >&2; return 1; }
  rm -rf "$DIR"
}

test_project_init_creates_subdirs() {
  DIR=$(mktemp -d)
  "$PROJECT_STORAGE" project init --name "test" --description "Test" --path "$DIR" > /dev/null
  for subdir in schedule todos issues concerns dependencies decisions; do
    [[ -d "$DIR/.dev-team-project/$subdir" ]] || { echo "missing subdir: $subdir" >&2; rm -rf "$DIR"; return 1; }
  done
  rm -rf "$DIR"
}

test_project_init_duplicate_fails() {
  DIR=$(mktemp -d)
  "$PROJECT_STORAGE" project init --name "test" --description "Test" --path "$DIR" > /dev/null
  if "$PROJECT_STORAGE" project init --name "test" --description "Test" --path "$DIR" 2>/dev/null; then
    echo "expected failure for duplicate init" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_project_status() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" project status --project "$DIR")
  assert_json_field "$OUTPUT" ".name" "test-project"
  assert_json_field "$OUTPUT" ".item_counts.todos" "0"
  assert_json_field "$OUTPUT" ".item_counts.issues" "0"
  rm -rf "$DIR"
}

test_project_link_cookbook() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-a" > /dev/null
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-b" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" project status --project "$DIR")
  COUNT=$(echo "$OUTPUT" | jq '.cookbook_projects | length')
  assert_eq "$COUNT" "2" "should have 2 linked cookbooks"
  rm -rf "$DIR"
}

test_project_link_cookbook_deduplicates() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-a" > /dev/null
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-a" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" project status --project "$DIR")
  COUNT=$(echo "$OUTPUT" | jq '.cookbook_projects | length')
  assert_eq "$COUNT" "1" "should deduplicate"
  rm -rf "$DIR"
}

test_project_unlink_cookbook() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-a" > /dev/null
  "$PROJECT_STORAGE" project link-cookbook --project "$DIR" --path "/tmp/cookbook-b" > /dev/null
  "$PROJECT_STORAGE" project unlink-cookbook --project "$DIR" --path "/tmp/cookbook-a" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" project status --project "$DIR")
  COUNT=$(echo "$OUTPUT" | jq '.cookbook_projects | length')
  assert_eq "$COUNT" "1" "should have 1 after unlink"

  REMAINING=$(echo "$OUTPUT" | jq -r '.cookbook_projects[0]')
  assert_eq "$REMAINING" "/tmp/cookbook-b" "should keep cookbook-b"
  rm -rf "$DIR"
}

test_project_init_missing_flags() {
  DIR=$(mktemp -d)
  if "$PROJECT_STORAGE" project init --name "test" --path "$DIR" 2>/dev/null; then
    echo "expected failure for missing --description" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

test_project_status_nonexistent() {
  if "$PROJECT_STORAGE" project status --project "/tmp/nonexistent-$$" 2>/dev/null; then
    echo "expected failure for nonexistent project" >&2
    return 1
  fi
}

run_test "project init creates manifest" test_project_init
run_test "project init creates subdirectories" test_project_init_creates_subdirs
run_test "project init fails on duplicate" test_project_init_duplicate_fails
run_test "project status returns manifest + counts" test_project_status
run_test "project link-cookbook adds paths" test_project_link_cookbook
run_test "project link-cookbook deduplicates" test_project_link_cookbook_deduplicates
run_test "project unlink-cookbook removes path" test_project_unlink_cookbook
run_test "project init fails with missing flags" test_project_init_missing_flags
run_test "project status fails for nonexistent" test_project_status_nonexistent

test_summary
