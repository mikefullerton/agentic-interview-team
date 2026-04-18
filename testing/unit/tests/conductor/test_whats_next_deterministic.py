"""Unit tests for `deterministic_short_circuit` — no LLM.

Exercises each branch of the rule set:
- empty roadmap → None
- open session-level gate → None
- active state rows present → None
- all nodes done → `done`
- exactly one runnable primitive → `advance-to` deterministic
- one runnable but has open gate → None
- one runnable but has in-flight request → None
- multiple runnable → None (fall through to LLM)
- one runnable compound → `decompose` deterministic
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.specialty.whats_next import (  # noqa: E402
    WhatsNextContext,
    deterministic_short_circuit,
)


def _node(node_id: str, *, kind: str = "primitive", title: str = "n") -> dict:
    return {
        "node_id": node_id,
        "title": title,
        "node_kind": kind,
        "specialist": None,
        "speciality": None,
    }


def _ctx(**kwargs) -> WhatsNextContext:
    defaults = dict(
        session_id="sess-1",
        roadmap_id="rm-1",
        plan_nodes=[],
        dependencies=[],
        latest_state_by_node={},
        active_state_rows=[],
        open_gates=[],
        in_flight_requests=[],
    )
    defaults.update(kwargs)
    return WhatsNextContext(**defaults)


def test_empty_roadmap_returns_none():
    assert deterministic_short_circuit(_ctx(roadmap_id=None)) is None
    assert deterministic_short_circuit(_ctx(plan_nodes=[])) is None


def test_open_session_level_gate_returns_none():
    ctx = _ctx(
        plan_nodes=[_node("a")],
        open_gates=[{"gate_id": "g1", "plan_node_id": None}],
    )
    assert deterministic_short_circuit(ctx) is None


def test_active_state_rows_force_llm():
    ctx = _ctx(
        plan_nodes=[_node("a")],
        active_state_rows=[{"state_id": "s1", "state_name": "dispatch"}],
    )
    assert deterministic_short_circuit(ctx) is None


def test_all_nodes_done_returns_done_action():
    ctx = _ctx(
        plan_nodes=[_node("a"), _node("b")],
        latest_state_by_node={"a": "done", "b": "done"},
    )
    decision = deterministic_short_circuit(ctx)
    assert decision is not None
    assert decision.action == "done"
    assert decision.deterministic is True


def test_single_runnable_primitive_returns_advance_to():
    ctx = _ctx(plan_nodes=[_node("a", title="start")])
    decision = deterministic_short_circuit(ctx)
    assert decision is not None
    assert decision.action == "advance-to"
    assert decision.node_id == "a"
    assert decision.deterministic is True


def test_linear_chain_walks_one_node_at_a_time():
    # A → B → C. Only A is runnable until A is done.
    nodes = [_node("a"), _node("b"), _node("c")]
    deps = [
        {"node_id": "b", "depends_on_id": "a"},
        {"node_id": "c", "depends_on_id": "b"},
    ]
    # Start: only A is runnable.
    d = deterministic_short_circuit(_ctx(plan_nodes=nodes, dependencies=deps))
    assert d is not None and d.node_id == "a"

    # A done: only B is runnable.
    d = deterministic_short_circuit(
        _ctx(
            plan_nodes=nodes,
            dependencies=deps,
            latest_state_by_node={"a": "done"},
        )
    )
    assert d is not None and d.node_id == "b"


def test_runnable_with_open_gate_defers_to_llm():
    ctx = _ctx(
        plan_nodes=[_node("a")],
        open_gates=[{"gate_id": "g1", "plan_node_id": "a"}],
    )
    # Open gate on the only runnable node — we filter that node out, so
    # no runnable nodes remain → fall through to LLM.
    assert deterministic_short_circuit(ctx) is None


def test_runnable_with_in_flight_request_defers_to_llm():
    ctx = _ctx(
        plan_nodes=[_node("a")],
        in_flight_requests=[
            {"request_id": "r1", "plan_node_id": "a", "status": "in-flight"}
        ],
    )
    assert deterministic_short_circuit(ctx) is None


def test_multiple_runnable_defers_to_llm():
    # Diamond: A → {B, C} → D. With A done, both B and C are runnable.
    nodes = [_node("a"), _node("b"), _node("c"), _node("d")]
    deps = [
        {"node_id": "b", "depends_on_id": "a"},
        {"node_id": "c", "depends_on_id": "a"},
        {"node_id": "d", "depends_on_id": "b"},
        {"node_id": "d", "depends_on_id": "c"},
    ]
    ctx = _ctx(
        plan_nodes=nodes,
        dependencies=deps,
        latest_state_by_node={"a": "done"},
    )
    assert deterministic_short_circuit(ctx) is None


def test_single_runnable_compound_returns_decompose():
    ctx = _ctx(plan_nodes=[_node("a", kind="compound")])
    d = deterministic_short_circuit(ctx)
    assert d is not None
    assert d.action == "decompose"
    assert d.node_id == "a"
    assert d.deterministic is True
