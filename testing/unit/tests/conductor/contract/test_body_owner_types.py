"""Body side-table contract — narrative content for every owner_type
the PR #13 migration introduced.

Existing test_arbitrator_roadmap_api.py covers plan_node + message. This
file adds finding, decision, and verifies the no-FK-enforcement contract
(body.owner_id is deliberately not FK'd to allow forward references and
inserts ahead of primary rows during schema evolution).
"""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import BodyFormat, NodeKind


@pytest.fixture
def connected_arb(tmp_path, run_async):
    arb = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(arb.start())
    yield arb
    run_async(arb.close())


def test_body_works_for_finding_owner(connected_arb, run_async, session_id):
    arb = connected_arb
    run_async(arb.open_session(session_id, initial_team_id="t"))
    result = run_async(arb.create_result(
        session_id=session_id, team_id="t", specialist_id="sp",
        passed=True, summary={},
    ))
    run_async(arb.create_finding(
        result_id=result.result_id, kind="note", severity="info",
        body="The narrative finding prose goes here.",
    ))
    # Look up body via side-table.
    rows = run_async(arb._storage.fetch_all("finding", where={"result_id": result.result_id}))
    body = run_async(arb.get_body("finding", rows[0]["finding_id"]))
    assert body is not None
    assert body.body_text == "The narrative finding prose goes here."


def test_body_works_for_decision_owner(connected_arb, run_async, session_id):
    arb = connected_arb
    run_async(arb.open_session(session_id, initial_team_id="pm"))
    decision = run_async(arb.create_decision_item(
        session_id=session_id, team_id="pm",
        title="Use SwiftUI", rationale="Better macOS+iOS story.",
        decided_by="user",
    ))
    body = run_async(arb.get_body("decision", decision["decision_id"]))
    assert body is not None
    assert body.body_text == "Better macOS+iOS story."


def test_body_works_for_plan_node_owner(connected_arb, run_async):
    arb = connected_arb
    rm = run_async(arb.create_roadmap("R"))
    node = run_async(arb.create_plan_node(
        rm.roadmap_id, "N", NodeKind.COMPOUND, node_id="n1",
    ))
    run_async(arb.set_body(
        "plan_node", node.node_id,
        "# Feature X\n\nDescribe the feature here.",
        body_format=BodyFormat.MARKDOWN,
    ))
    back = run_async(arb.get_body("plan_node", node.node_id))
    assert back.body_format == BodyFormat.MARKDOWN
    assert back.body_text.startswith("# Feature X")


def test_body_owner_id_is_not_fk_constrained(sqlite_conn, iso_now):
    """Body must accept an owner_id that no primary row currently uses.
    This is deliberate — body rows can precede their owner during bulk
    inserts — and changing it would break schema evolution."""
    sqlite_conn.execute(
        "INSERT INTO body (owner_type, owner_id, body_format, body_text, modification_date) "
        "VALUES ('plan_node', 'node-never-created', 'markdown', 'ghost body', ?)",
        (iso_now,),
    )
    sqlite_conn.commit()
    row = sqlite_conn.execute(
        "SELECT body_text FROM body "
        "WHERE owner_type='plan_node' AND owner_id='node-never-created'"
    ).fetchone()
    assert row[0] == "ghost body"


def test_body_is_upsert_across_calls(connected_arb, run_async):
    arb = connected_arb
    run_async(arb.set_body("plan_node", "nX", "v1"))
    run_async(arb.set_body("plan_node", "nX", "v2"))
    run_async(arb.set_body("plan_node", "nX", "v3"))
    back = run_async(arb.get_body("plan_node", "nX"))
    assert back.body_text == "v3"

    # Different owner_type with same owner_id must not collide.
    run_async(arb.set_body("finding", "nX", "finding-body"))
    assert run_async(arb.get_body("plan_node", "nX")).body_text == "v3"
    assert run_async(arb.get_body("finding",   "nX")).body_text == "finding-body"


def test_body_format_round_trips(connected_arb, run_async):
    arb = connected_arb
    run_async(arb.set_body("plan_node", "nA", "plain prose",
                           body_format=BodyFormat.PLAIN))
    run_async(arb.set_body("plan_node", "nB", "# md",
                           body_format=BodyFormat.MARKDOWN))
    run_async(arb.set_body("plan_node", "nC", "{\"k\": 1}",
                           body_format=BodyFormat.JSON))
    assert run_async(arb.get_body("plan_node", "nA")).body_format == BodyFormat.PLAIN
    assert run_async(arb.get_body("plan_node", "nB")).body_format == BodyFormat.MARKDOWN
    assert run_async(arb.get_body("plan_node", "nC")).body_format == BodyFormat.JSON
