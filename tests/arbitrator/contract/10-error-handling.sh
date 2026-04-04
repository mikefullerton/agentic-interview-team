#!/bin/bash
# 10-error-handling.sh — Contract tests for error handling across all resources
set -euo pipefail

source "$(dirname "$0")/../lib/test-helpers.sh"

# -- Tests --

test_unknown_resource() {
  if "$ARBITRATOR" foobar create 2>/dev/null; then
    echo "expected failure for unknown resource" >&2
    return 1
  fi
}

test_unknown_action() {
  if "$ARBITRATOR" session foobar 2>/dev/null; then
    echo "expected failure for unknown action" >&2
    return 1
  fi
}

test_missing_resource() {
  if "$ARBITRATOR" 2>/dev/null; then
    echo "expected failure for missing resource" >&2
    return 1
  fi
}

test_state_append_nonexistent_session() {
  if "$ARBITRATOR" state append \
    --session "nonexistent" --changed-by test --state running 2>/dev/null; then
    echo "expected failure for nonexistent session" >&2
    return 1
  fi
}

test_finding_get_nonexistent() {
  if "$ARBITRATOR" finding get --finding "nonexistent:finding:x:0001" 2>/dev/null; then
    echo "expected failure for nonexistent finding" >&2
    return 1
  fi
}

test_report_overview_nonexistent_session() {
  if "$ARBITRATOR" report overview --session "nonexistent" 2>/dev/null; then
    echo "expected failure for nonexistent session" >&2
    return 1
  fi
}

# -- Run --

run_test "unknown resource fails" test_unknown_resource
run_test "unknown action fails" test_unknown_action
run_test "missing resource arg fails" test_missing_resource
run_test "state append on nonexistent session fails" test_state_append_nonexistent_session
run_test "finding get for nonexistent finding fails" test_finding_get_nonexistent
run_test "report overview on nonexistent session fails" test_report_overview_nonexistent_session

test_summary
