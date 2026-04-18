"""The LIVE conductor schema must pass every check in schema_lint.py.

If this breaks, either the schema drifted from .claude/rules/db-schema-design.md
or a new rule was added. Investigate the named violation, not this test.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
LINT_SCRIPT = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db" / "schema_lint.py"


def _load_linter():
    sys.path.insert(0, str(LINT_SCRIPT.parent))
    try:
        import schema_lint
    finally:
        sys.path.pop(0)
    return schema_lint


def test_live_schema_produces_no_violations(live_schema_sql):
    linter = _load_linter()
    violations = linter.lint(live_schema_sql)
    assert violations == [], (
        "live conductor schema violates db-schema-design.md:\n  "
        + "\n  ".join(violations)
    )


def test_all_five_checks_run(live_schema_sql):
    """The linter exposes five named checks; every one must actually run."""
    linter = _load_linter()
    names = [name for name, _fn in linter.CHECKS]
    assert names == [
        "no *_at date naming",
        "no blob columns in primary tables",
        "entity tables have creation_date",
        "plan_node_id join key present",
        "body side-table shape",
    ]


def test_linter_catches_injected_violation(live_schema_sql):
    """Sanity: if we deliberately inject a *_at column, the linter flags it."""
    linter = _load_linter()
    mutated = live_schema_sql + "\nCREATE TABLE _probe (probe_id TEXT PRIMARY KEY, probe_at TEXT);\n"
    violations = linter.lint(mutated)
    assert any("probe_at" in v for v in violations), (
        f"linter did not catch injected *_at column; got: {violations}"
    )
