#!/usr/bin/env python3
"""Deterministic test runner — iterates every test area in fixed order."""

import subprocess
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).parent
UNIT_DIR = HARNESS_DIR.parent
TESTS_DIR = UNIT_DIR / "tests"

AREAS = [
    ("atp",              "testing/unit/tests/atp"),
    ("arbitrator",       "testing/unit/tests/arbitrator"),
    ("project-storage",  "testing/unit/tests/project-storage"),
    ("specialty-teams",  "testing/unit/tests/specialty-teams"),
    ("consulting-teams", "testing/unit/tests/consulting-teams"),
    ("agents",           "testing/unit/tests/agents"),
    ("specialists",      "testing/unit/tests/specialists"),
    ("skills",           "testing/unit/tests/skills"),
    ("observers",        "testing/unit/tests/observers"),
    ("session",          "testing/unit/tests/session"),
    ("dashboard",        "testing/unit/tests/dashboard"),
    ("harness",          "testing/unit/harness/test_assertions.py testing/unit/harness/test_fixtures.py"),
]


def main():
    results = []
    any_failed = False

    for name, path in AREAS:
        paths = path.split()
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + paths + ["-q", "--tb=short"],
            capture_output=True,
            text=True,
        )
        # Parse the summary line for counts
        summary = ""
        for line in result.stdout.strip().split(chr(10)):
            if "passed" in line or "failed" in line or "error" in line:
                summary = line.strip()

        passed = failed = skipped = 0
        import re
        m = re.search(r"(\d+) passed", summary)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) failed", summary)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+) skipped", summary)
        if m:
            skipped = int(m.group(1))

        status = "PASS" if result.returncode == 0 else "FAIL"
        if status == "FAIL":
            any_failed = True

        results.append((name, passed, failed, skipped, status))

        icon = "✓" if status == "PASS" else "✗"
        skip_note = f" ({skipped} skipped)" if skipped else ""
        print(f"  {icon} {name:<20s} {passed:>5d} passed{skip_note}")

        if result.returncode != 0:
            # Show failure details
            for line in result.stdout.strip().split(chr(10)):
                if "FAILED" in line:
                    print(f"    {line.strip()}")

    # Summary
    total_passed = sum(r[1] for r in results)
    total_failed = sum(r[2] for r in results)
    total_skipped = sum(r[3] for r in results)
    total = total_passed + total_failed

    print()
    print(f"  {len(AREAS)} areas, {total} tests, {total_passed} passed, {total_failed} failed, {total_skipped} skipped")

    if any_failed:
        print()
        print("  FAILED areas:")
        for name, _, failed, _, status in results:
            if status == "FAIL":
                print(f"    - {name} ({failed} failures)")
        sys.exit(1)
    else:
        print("  All areas passed.")


if __name__ == "__main__":
    main()
