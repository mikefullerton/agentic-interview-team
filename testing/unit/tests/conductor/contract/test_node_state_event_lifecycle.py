"""Lifecycle contract for node_state_event.

Existing test_arbitrator_roadmap_api.py covers 4 of the 6 event types
(planned/ready/running/done). This file covers failed and superseded,
asserts ordering, and pins `latest_node_state` semantics including
re-decomposition (superseded → planned).
"""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import NodeKind, NodeStateEventType


@pytest.fixture
def node_arb(tmp_path, run_async):
    arb = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(arb.start())
    rm = run_async(arb.create_roadmap("R"))
    node = run_async(arb.create_plan_node(
        rm.roadmap_id, "N", NodeKind.PRIMITIVE, node_id="node-1",
    ))
    yield arb, node
    run_async(arb.close())


def test_all_six_event_types_write_and_read_back(node_arb, run_async):
    arb, node = node_arb
    for et in (
        NodeStateEventType.PLANNED,
        NodeStateEventType.READY,
        NodeStateEventType.RUNNING,
        NodeStateEventType.DONE,
        NodeStateEventType.FAILED,
        NodeStateEventType.SUPERSEDED,
    ):
        run_async(arb.record_node_state_event(node.node_id, et, actor="exec"))

    latest = run_async(arb.latest_node_state(node.node_id))
    assert latest.event_type == NodeStateEventType.SUPERSEDED


def test_failed_is_terminal_until_overwritten(node_arb, run_async):
    arb, node = node_arb
    run_async(arb.record_node_state_event(node.node_id, NodeStateEventType.RUNNING, actor="e"))
    run_async(arb.record_node_state_event(node.node_id, NodeStateEventType.FAILED, actor="e"))
    latest = run_async(arb.latest_node_state(node.node_id))
    assert latest.event_type == NodeStateEventType.FAILED


def test_superseded_followed_by_planned_reopens_node(node_arb, run_async):
    """Re-decomposition writes superseded then re-planned. latest_node_state
    must reflect the re-planned status so the scheduler can pick it up again."""
    arb, node = node_arb
    for et in (
        NodeStateEventType.PLANNED,
        NodeStateEventType.READY,
        NodeStateEventType.RUNNING,
        NodeStateEventType.DONE,
        NodeStateEventType.SUPERSEDED,
        NodeStateEventType.PLANNED,
    ):
        run_async(arb.record_node_state_event(node.node_id, et, actor="executor"))
    latest = run_async(arb.latest_node_state(node.node_id))
    assert latest.event_type == NodeStateEventType.PLANNED


def test_event_date_order_matches_insertion_order(sqlite_conn, seed_roadmap, seed_node, iso_now):
    """Append-only log: event_id monotonically increases, preserving order
    of insertion even when event_date ties."""
    rm = seed_roadmap()
    seed_node("n", rm, position=1.0)
    for et in ("planned", "ready", "running", "failed", "superseded", "planned"):
        sqlite_conn.execute(
            "INSERT INTO node_state_event (node_id, event_type, actor, event_date) "
            "VALUES ('n', ?, 'exec', ?)", (et, iso_now),
        )
    sqlite_conn.commit()
    rows = sqlite_conn.execute(
        "SELECT event_type FROM node_state_event WHERE node_id='n' ORDER BY event_id"
    ).fetchall()
    assert [r[0] for r in rows] == [
        "planned", "ready", "running", "failed", "superseded", "planned",
    ]


def test_session_id_on_event_is_optional(sqlite_conn, seed_roadmap, seed_node, iso_now):
    """NULL session_id is accepted — project-scoped events may have no session."""
    rm = seed_roadmap()
    seed_node("n", rm, position=1.0)
    sqlite_conn.execute(
        "INSERT INTO node_state_event (node_id, session_id, event_type, actor, event_date) "
        "VALUES ('n', NULL, 'planned', 'planner', ?)", (iso_now,),
    )
    sqlite_conn.commit()
    row = sqlite_conn.execute(
        "SELECT session_id FROM node_state_event WHERE node_id='n'"
    ).fetchone()
    assert row[0] is None
