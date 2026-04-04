#!/bin/bash
# test-helpers.sh — Assertion library for arbitrator contract tests

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

repo_root() {
  git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel
}

ARBITRATOR="$(repo_root)/plugins/dev-team/scripts/arbitrator.sh"

# Run a test function and track results
run_test() {
  local name="$1"
  local func="$2"
  TESTS_RUN=$((TESTS_RUN + 1))
  if $func 2>/dev/null; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "  PASS: ${name}"
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "  FAIL: ${name}"
  fi
}

# Print test summary and exit with appropriate code
test_summary() {
  echo ""
  echo "  ${TESTS_PASSED}/${TESTS_RUN} passed, ${TESTS_FAILED} failed"
  [[ $TESTS_FAILED -eq 0 ]] && return 0 || return 1
}

assert_exit_0() {
  local code="$1"
  if [[ "$code" -ne 0 ]]; then
    echo "expected exit 0, got ${code}" >&2
    return 1
  fi
}

assert_eq() {
  local actual="$1" expected="$2" msg="${3:-values should match}"
  if [[ "$actual" != "$expected" ]]; then
    echo "${msg}: expected '${expected}', got '${actual}'" >&2
    return 1
  fi
}

assert_not_empty() {
  local value="$1" msg="${2:-value should not be empty}"
  if [[ -z "$value" || "$value" == "null" ]]; then
    echo "${msg}: value is empty or null" >&2
    return 1
  fi
}

assert_json_field() {
  local json="$1" field="$2" expected="$3"
  local actual
  actual=$(echo "$json" | jq -r "$field")
  assert_eq "$actual" "$expected" "JSON field ${field}"
}

assert_json_count() {
  local json="$1" expected="$2" msg="${3:-array length}"
  local actual
  actual=$(echo "$json" | jq 'length')
  assert_eq "$actual" "$expected" "$msg"
}

assert_json_not_empty() {
  local json="$1" field="$2" msg="${3:-JSON field should not be empty}"
  local actual
  actual=$(echo "$json" | jq -r "$field")
  assert_not_empty "$actual" "$msg"
}
