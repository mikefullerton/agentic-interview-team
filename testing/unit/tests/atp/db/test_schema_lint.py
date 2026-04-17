"""Schema conformance linter passes on schema-v3 and catches violations."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_DB = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db"

# Import the linter module directly; it lives in a non-package directory.
sys.path.insert(0, str(SCRIPTS_DB))
import schema_lint  # noqa: E402


SCHEMA_PATH = SCRIPTS_DB / "schema-v3.sql"


def test_schema_v3_is_clean():
    violations = schema_lint.lint(SCHEMA_PATH.read_text())
    assert violations == [], "schema-v3.sql has violations:\n" + "\n".join(violations)


def test_lint_catches_at_suffix():
    schema = """
    CREATE TABLE widget (
        widget_id TEXT PRIMARY KEY,
        created_at DATETIME NOT NULL
    );
    CREATE TABLE body (
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        body_format TEXT NOT NULL,
        body_text TEXT NOT NULL,
        modification_date DATETIME NOT NULL,
        PRIMARY KEY (owner_type, owner_id)
    );
    """
    violations = schema_lint.lint(schema)
    assert any("created_at" in v for v in violations)


def test_lint_catches_blob_column():
    schema = """
    CREATE TABLE widget (
        widget_id TEXT PRIMARY KEY,
        summary TEXT NOT NULL,
        creation_date DATETIME NOT NULL
    );
    CREATE TABLE body (
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        body_format TEXT NOT NULL,
        body_text TEXT NOT NULL,
        modification_date DATETIME NOT NULL,
        PRIMARY KEY (owner_type, owner_id)
    );
    """
    violations = schema_lint.lint(schema)
    assert any("widget.summary" in v for v in violations), violations


def test_lint_catches_json_suffix():
    schema = """
    CREATE TABLE widget (
        widget_id TEXT PRIMARY KEY,
        metadata_json TEXT NOT NULL,
        creation_date DATETIME NOT NULL
    );
    CREATE TABLE body (
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        body_format TEXT NOT NULL,
        body_text TEXT NOT NULL,
        modification_date DATETIME NOT NULL,
        PRIMARY KEY (owner_type, owner_id)
    );
    """
    violations = schema_lint.lint(schema)
    assert any("metadata_json" in v for v in violations), violations


def test_lint_catches_missing_body_table():
    schema = """
    CREATE TABLE widget (
        widget_id TEXT PRIMARY KEY,
        creation_date DATETIME NOT NULL
    );
    """
    violations = schema_lint.lint(schema)
    assert any("body" in v and "side-table" in v for v in violations), violations


def test_lint_catches_body_table_wrong_shape():
    schema = """
    CREATE TABLE widget (
        widget_id TEXT PRIMARY KEY,
        creation_date DATETIME NOT NULL
    );
    CREATE TABLE body (
        body_id TEXT PRIMARY KEY,
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        body_format TEXT NOT NULL,
        body_text TEXT NOT NULL,
        modification_date DATETIME NOT NULL
    );
    """
    violations = schema_lint.lint(schema)
    assert any("composite primary key" in v for v in violations), violations


def test_lint_reports_schema_load_errors():
    violations = schema_lint.lint("THIS IS NOT VALID SQL ;")
    assert violations and "SCHEMA LOAD FAILED" in violations[0]


def test_lint_cli_exit_zero_on_clean(tmp_path):
    """Invoking the CLI on schema-v3 should exit 0."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DB / "schema_lint.py"), str(SCHEMA_PATH)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"lint failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_lint_cli_exit_nonzero_on_violations(tmp_path):
    """Invoking the CLI on a bad schema should exit 1."""
    bad_schema = tmp_path / "bad.sql"
    bad_schema.write_text("""
        CREATE TABLE widget (
            widget_id TEXT PRIMARY KEY,
            created_at DATETIME NOT NULL
        );
    """)
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DB / "schema_lint.py"), str(bad_schema)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "created_at" in result.stdout
