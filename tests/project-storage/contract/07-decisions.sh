#!/bin/bash
# 07-decisions.sh — Contract tests for decision resource
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

test_decision_create_returns_id() {
  DIR=$(new_project)
  OUTPUT=$("$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Use PostgreSQL" \
    --description "We will use PostgreSQL as the primary database" \
    --rationale "Strong ACID compliance and JSON support" \
    --made-by "architecture-team")
  assert_json_not_empty "$OUTPUT" ".id" "id should not be empty"
  rm -rf "$DIR"
}

test_decision_get_returns_all_fields() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Use TypeScript" \
    --description "Adopt TypeScript across the codebase" \
    --rationale "Type safety reduces runtime errors" \
    --made-by "tech-lead" | jq -r '.id')

  OUTPUT=$("$PROJECT_STORAGE" decision get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".id" "$ID"
  assert_json_field "$OUTPUT" ".title" "Use TypeScript"
  assert_json_field "$OUTPUT" ".rationale" "Type safety reduces runtime errors"
  assert_json_field "$OUTPUT" ".made_by" "tech-lead"
  assert_json_not_empty "$OUTPUT" ".description" "description should not be empty"
  assert_json_not_empty "$OUTPUT" ".date" "date should not be empty"
  assert_json_not_empty "$OUTPUT" ".created" "created should not be empty"
  assert_json_not_empty "$OUTPUT" ".modified" "modified should not be empty"
  rm -rf "$DIR"
}

test_decision_create_with_optional_alternatives_and_date() {
  DIR=$(new_project)
  ID=$("$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Choose Deployment Platform" \
    --description "Selected AWS over GCP and Azure" \
    --rationale "Existing team expertise and cost structure" \
    --made-by "cto" \
    --alternatives "GCP, Azure" \
    --date "2024-01-15" | jq -r '.id')

  OUTPUT=$("$PROJECT_STORAGE" decision get --project "$DIR" --id "$ID")
  assert_json_field "$OUTPUT" ".alternatives" "GCP, Azure"
  assert_json_field "$OUTPUT" ".date" "2024-01-15"
  rm -rf "$DIR"
}

test_decision_list_returns_all_decisions() {
  DIR=$(new_project)
  "$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Decision Alpha" \
    --description "First decision" \
    --rationale "Because alpha" \
    --made-by "team" > /dev/null
  "$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Decision Beta" \
    --description "Second decision" \
    --rationale "Because beta" \
    --made-by "team" > /dev/null

  OUTPUT=$("$PROJECT_STORAGE" decision list --project "$DIR")
  assert_json_count "$OUTPUT" "2" "should return 2 decisions"
  rm -rf "$DIR"
}

test_decision_create_fails_missing_flags() {
  DIR=$(new_project)
  # Missing --rationale and --made-by
  if "$PROJECT_STORAGE" decision create \
    --project "$DIR" \
    --title "Incomplete Decision" \
    --description "Missing required flags" 2>/dev/null; then
    echo "expected failure for missing flags" >&2
    rm -rf "$DIR"
    return 1
  fi
  rm -rf "$DIR"
}

run_test "decision create returns id" test_decision_create_returns_id
run_test "decision get returns all fields including description" test_decision_get_returns_all_fields
run_test "decision create with optional alternatives and date" test_decision_create_with_optional_alternatives_and_date
run_test "decision list returns all decisions" test_decision_list_returns_all_decisions
run_test "decision create fails with missing flags" test_decision_create_fails_missing_flags

test_summary
