"""Contract tests for error handling across all resources."""
import pytest
from arbitrator_helpers import run_arbitrator, make_session


def test_unknown_resource_fails():
    result = run_arbitrator("foobar", "create")
    assert result.returncode != 0


def test_unknown_action_fails():
    result = run_arbitrator("session", "foobar")
    assert result.returncode != 0


def test_missing_resource_arg_fails():
    result = run_arbitrator()
    assert result.returncode != 0


def test_state_append_on_nonexistent_session_fails():
    result = run_arbitrator("state", "append", "--session", "nonexistent", "--changed-by", "test", "--state", "running")
    assert result.returncode != 0


def test_finding_get_for_nonexistent_finding_fails():
    result = run_arbitrator("finding", "get", "--finding", "nonexistent:finding:x:0001")
    assert result.returncode != 0


def test_report_overview_on_nonexistent_session_fails():
    result = run_arbitrator("report", "overview", "--session", "nonexistent")
    assert result.returncode != 0
