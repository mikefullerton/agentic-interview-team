#!/bin/bash
# 06-dependencies.sh — Contract tests for dependency resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_dependency_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Auth Service" \
    --description "External auth provider" \
    --type "external" \
    --status "active")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_dependency_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Payment Gateway" \
    --description "Stripe integration for payments" \
    --type "external" \
    --status "active" | jq -r '.id')

  OUTPUT=$("$PROJECT_STORAGE" dependency get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".id" "$ID"
  assert_json_field "$OUTPUT" ".name" "Payment Gateway"
  assert_json_field "$OUTPUT" ".type" "external"
  assert_json_field "$OUTPUT" ".status" "active"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  assert_json_not_empty "$OUTPUT" ".modified" "modified should not be empty"
  rm -rf "$DIR"
}

test_dependency_list_returns_dependencies() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Dep One" \
    --description "First dependency" \
    --type "internal" \
    --status "active" > /dev/null
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Dep Two" \
    --description "Second dependency" \
    --type "external" \
    --status "pending" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" dependency list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should return 2 dependencies"
  rm -rf "$DIR"
}

test_dependency_list_filters_by_status() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Active Dep" \
    --description "An active dependency" \
    --type "external" \
    --status "active" > /dev/null
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Pending Dep" \
    --description "A pending dependency" \
    --type "external" \
    --status "pending" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" dependency list --project "$DIR" --status "active")
  assert_json_count "$OUTPUT" "1" "should return 1 active dependency"
  assert_json_field "$OUTPUT" ".[0].status" "active"
  rm -rf "$DIR"
}

test_dependency_list_filters_by_type() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Internal Dep" \
    --description "An internal dependency" \
    --type "internal" \
    --status "active" > /dev/null
  "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "External Dep" \
    --description "An external dependency" \
    --type "external" \
    --status "active" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" dependency list --project "$DIR" --type "internal")
  assert_json_count "$OUTPUT" "1" "should return 1 internal dependency"
  assert_json_field "$OUTPUT" ".[0].type" "internal"
  rm -rf "$DIR"
}

test_dependency_create_fails_missing_flags() {
  DIR=$(new_project)
  # Missing --type and --status
  if "$PROJECT_STORAGE" dependency create \
    --project "$DIR" \
    --name "Incomplete" \
    --description "Missing required flags" 2>/dev/null; then
    echo "expected failure for missing flags" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "dependency create returns id" test_dependency_create_returns_id
run_test "dependency get returns all fields including description" test_dependency_get_returns_all_fields
run_test "dependency list returns dependencies" test_dependency_list_returns_dependencies
run_test "dependency list filters by status" test_dependency_list_filters_by_status
run_test "dependency list filters by type" test_dependency_list_filters_by_type
run_test "dependency create fails with missing flags" test_dependency_create_fails_missing_flags

test_summary
