#!/bin/bash
# run-contract-tests.sh — Run all contract tests against each backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL_PASS=0
TOTAL_FAIL=0

REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
BACKENDS=()
for backend_dir in "$REPO_ROOT"/plugins/dev-team/scripts/project-storage/*/; do
  [[ -d "$backend_dir" ]] || continue
  BACKENDS+=("$(basename "$backend_dir")")
done

if [[ ${#BACKENDS[@]} -eq 0 ]]; then
  echo "No backends found in scripts/project-storage/" >&2
  exit 1
fi

for backend in "${BACKENDS[@]}"; do
  echo "=== Backend: ${backend} ==="

  export PROJECT_STORAGE_BACKEND="$backend"

  BACKEND_PASS=0
  BACKEND_FAIL=0

  for test_file in "$SCRIPT_DIR"/contract/*.sh; do
    [[ -f "$test_file" ]] || continue
    test_name=$(basename "$test_file" .sh)
    echo ""
    echo "--- ${test_name} ---"

    if bash "$test_file"; then
      BACKEND_PASS=$((BACKEND_PASS + 1))
    else
      BACKEND_FAIL=$((BACKEND_FAIL + 1))
    fi
  done

  echo ""
  echo "=== ${backend}: ${BACKEND_PASS} suites passed, ${BACKEND_FAIL} failed ==="
  echo ""

  TOTAL_PASS=$((TOTAL_PASS + BACKEND_PASS))
  TOTAL_FAIL=$((TOTAL_FAIL + BACKEND_FAIL))
done

echo "Total: ${TOTAL_PASS} suites passed, ${TOTAL_FAIL} failed"
[[ $TOTAL_FAIL -eq 0 ]] && exit 0 || exit 1
