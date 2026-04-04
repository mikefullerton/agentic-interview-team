"""Contract tests for message and gate-option resources."""
import pytest
from arbitrator_helpers import run_arbitrator, run_ok, run_json, make_session


def test_message_send_creates_a_record():
    session_id = make_session()

    result = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "finding",
        "--changed-by", "analyst",
        "--content", "Initial analysis complete",
    )
    assert result["session_id"] == session_id
    assert result["type"] == "finding"
    assert result["changed_by"] == "analyst"
    assert result["content"] == "Initial analysis complete"
    assert result["id"]
    assert result["creation_date"]


def test_message_send_id_is_composite():
    session_id = make_session()

    result = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "finding",
        "--changed-by", "analyst",
        "--content", "Test message",
    )
    assert result["id"].startswith(f"{session_id}:message:")


def test_message_send_with_optional_fields():
    session_id = make_session()

    result = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "finding",
        "--changed-by", "security-specialist",
        "--content", "SQL injection risk detected",
        "--specialist", "security",
        "--category", "vulnerability",
        "--severity", "high",
    )
    assert result["specialist"] == "security"
    assert result["category"] == "vulnerability"
    assert result["severity"] == "high"


def test_message_list_returns_all_messages():
    session_id = make_session()

    run_ok("message", "send", "--session", session_id, "--type", "finding", "--changed-by", "analyst", "--content", "First")
    run_ok("message", "send", "--session", session_id, "--type", "gate", "--changed-by", "orchestrator", "--content", "Gate check")
    run_ok("message", "send", "--session", session_id, "--type", "finding", "--changed-by", "analyst", "--content", "Third")

    result = run_json("message", "list", "--session", session_id)
    assert len(result) == 3


def test_message_list_filters_by_type():
    session_id = make_session()

    run_ok("message", "send", "--session", session_id, "--type", "finding", "--changed-by", "analyst", "--content", "Finding 1")
    run_ok("message", "send", "--session", session_id, "--type", "gate", "--changed-by", "orchestrator", "--content", "Gate 1")
    run_ok("message", "send", "--session", session_id, "--type", "finding", "--changed-by", "analyst", "--content", "Finding 2")

    findings = run_json("message", "list", "--session", session_id, "--type", "finding")
    assert len(findings) == 2

    gates = run_json("message", "list", "--session", session_id, "--type", "gate")
    assert len(gates) == 1


def test_message_get_retrieves_by_id():
    session_id = make_session()

    sent = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "finding",
        "--changed-by", "analyst",
        "--content", "Findable message",
    )
    msg_id = sent["id"]

    result = run_json("message", "get", "--message", msg_id)
    assert result["id"] == msg_id
    assert result["content"] == "Findable message"


def test_gate_option_add_creates_an_option_linked_to_a_message():
    session_id = make_session()

    msg = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "gate",
        "--changed-by", "orchestrator",
        "--content", "Choose an option",
    )
    msg_id = msg["id"]

    result = run_json(
        "gate-option", "add",
        "--message", msg_id,
        "--option-text", "Continue",
        "--is-default", "1",
        "--sort-order", "1",
    )
    assert result["message_id"] == msg_id
    assert result["option_text"] == "Continue"
    assert str(result["is_default"]) == "1"
    assert str(result["sort_order"]) == "1"
    assert result["id"]


def test_gate_option_add_supports_multiple_options_per_message():
    session_id = make_session()

    msg = run_json(
        "message", "send",
        "--session", session_id,
        "--type", "gate",
        "--changed-by", "orchestrator",
        "--content", "Multi-option gate",
    )
    msg_id = msg["id"]

    opt1 = run_json("gate-option", "add", "--message", msg_id, "--option-text", "Yes", "--is-default", "1", "--sort-order", "1")
    opt2 = run_json("gate-option", "add", "--message", msg_id, "--option-text", "No", "--is-default", "0", "--sort-order", "2")

    assert opt1["id"]
    assert opt2["id"]
    assert opt1["id"] != opt2["id"]


def test_message_send_fails_with_missing_required_flags():
    session_id = make_session()

    result = run_arbitrator(
        "message", "send",
        "--session", session_id,
        "--type", "finding",
        "--changed-by", "analyst",
    )
    assert result.returncode != 0


def test_message_list_returns_empty_for_new_session():
    session_id = make_session()

    result = run_json("message", "list", "--session", session_id)
    assert len(result) == 0
