"""Arbitrator API for roadmap resources: create, query, dependencies,
lifecycle events, body side-table.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.api import CycleError
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import (
    BodyFormat,
    NodeKind,
    NodeStateEventType,
)


@pytest.fixture
def connected_arb(tmp_path, run_async):
    """A connected Arbitrator on a fresh SQLite file."""
    arb = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(arb.start())
    yield arb
    run_async(arb.close())


def test_create_and_get_roadmap(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("My Project"))
    assert rm.title == "My Project"
    assert rm.roadmap_id.startswith("rm_")
    back = run_async(connected_arb.get_roadmap(rm.roadmap_id))
    assert back is not None
    assert back.title == "My Project"


def test_get_missing_roadmap_returns_none(connected_arb, run_async):
    assert run_async(connected_arb.get_roadmap("does-not-exist")) is None


def test_create_plan_node(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    node = run_async(
        connected_arb.create_plan_node(
            rm.roadmap_id, "Feature X", NodeKind.COMPOUND,
            specialist="software-architecture",
        )
    )
    assert node.title == "Feature X"
    assert node.node_kind == NodeKind.COMPOUND
    assert node.specialist == "software-architecture"
    assert node.parent_id is None
    assert node.position == 1.0


def test_list_plan_nodes(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    for i, t in enumerate(["a", "b", "c"]):
        run_async(connected_arb.create_plan_node(
            rm.roadmap_id, t, NodeKind.PRIMITIVE, position=float(i),
        ))
    nodes = run_async(connected_arb.list_plan_nodes(rm.roadmap_id))
    titles = [n.title for n in nodes]
    assert titles == ["a", "b", "c"]


def test_list_plan_nodes_by_parent(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    root = run_async(connected_arb.create_plan_node(
        rm.roadmap_id, "root", NodeKind.COMPOUND,
    ))
    child1 = run_async(connected_arb.create_plan_node(
        rm.roadmap_id, "child1", NodeKind.PRIMITIVE,
        parent_id=root.node_id, position=1.0,
    ))
    child2 = run_async(connected_arb.create_plan_node(
        rm.roadmap_id, "child2", NodeKind.PRIMITIVE,
        parent_id=root.node_id, position=2.0,
    ))

    roots = run_async(connected_arb.list_plan_nodes_by_parent(rm.roadmap_id, None))
    assert [n.node_id for n in roots] == [root.node_id]
    children = run_async(
        connected_arb.list_plan_nodes_by_parent(rm.roadmap_id, root.node_id)
    )
    assert [n.title for n in children] == ["child1", "child2"]


def test_add_dependency_and_list(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE, position=1.0))
    b = run_async(connected_arb.create_plan_node(rm.roadmap_id, "b", NodeKind.PRIMITIVE, position=2.0))
    c = run_async(connected_arb.create_plan_node(rm.roadmap_id, "c", NodeKind.PRIMITIVE, position=3.0))

    run_async(connected_arb.add_dependency(a.node_id, b.node_id))
    run_async(connected_arb.add_dependency(a.node_id, c.node_id))

    deps = run_async(connected_arb.list_dependencies_of(a.node_id))
    targets = {d.depends_on_id for d in deps}
    assert targets == {b.node_id, c.node_id}


def test_add_dependency_detects_self_cycle(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE))
    with pytest.raises(CycleError):
        run_async(connected_arb.add_dependency(a.node_id, a.node_id))


def test_add_dependency_detects_direct_cycle(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE, position=1.0))
    b = run_async(connected_arb.create_plan_node(rm.roadmap_id, "b", NodeKind.PRIMITIVE, position=2.0))
    run_async(connected_arb.add_dependency(a.node_id, b.node_id))
    with pytest.raises(CycleError):
        run_async(connected_arb.add_dependency(b.node_id, a.node_id))


def test_add_dependency_detects_transitive_cycle(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE, position=1.0))
    b = run_async(connected_arb.create_plan_node(rm.roadmap_id, "b", NodeKind.PRIMITIVE, position=2.0))
    c = run_async(connected_arb.create_plan_node(rm.roadmap_id, "c", NodeKind.PRIMITIVE, position=3.0))
    run_async(connected_arb.add_dependency(a.node_id, b.node_id))
    run_async(connected_arb.add_dependency(b.node_id, c.node_id))
    with pytest.raises(CycleError):
        run_async(connected_arb.add_dependency(c.node_id, a.node_id))


def test_record_node_state_event(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE))

    for et in (NodeStateEventType.PLANNED, NodeStateEventType.READY, NodeStateEventType.RUNNING, NodeStateEventType.DONE):
        run_async(connected_arb.record_node_state_event(a.node_id, et, actor="executor"))

    latest = run_async(connected_arb.latest_node_state(a.node_id))
    assert latest is not None
    assert latest.event_type == NodeStateEventType.DONE


def test_latest_node_state_none_when_no_events(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE))
    assert run_async(connected_arb.latest_node_state(a.node_id)) is None


def test_record_event_with_session(connected_arb, run_async):
    rm = run_async(connected_arb.create_roadmap("rm"))
    a = run_async(connected_arb.create_plan_node(rm.roadmap_id, "a", NodeKind.PRIMITIVE))
    sess_id = uuid4()
    run_async(connected_arb.open_session(sess_id, "team"))
    ev = run_async(connected_arb.record_node_state_event(
        a.node_id, NodeStateEventType.RUNNING, actor="executor", session_id=sess_id,
    ))
    assert ev.session_id == sess_id


def test_set_and_get_body(connected_arb, run_async):
    body = run_async(connected_arb.set_body(
        "plan_node", "n1", "# Hello\n\nMarkdown content.",
        body_format=BodyFormat.MARKDOWN,
    ))
    assert body.body_text == "# Hello\n\nMarkdown content."
    assert body.body_format == BodyFormat.MARKDOWN

    back = run_async(connected_arb.get_body("plan_node", "n1"))
    assert back is not None
    assert back.body_text == "# Hello\n\nMarkdown content."


def test_set_body_is_upsert(connected_arb, run_async):
    run_async(connected_arb.set_body("plan_node", "n1", "v1"))
    run_async(connected_arb.set_body("plan_node", "n1", "v2"))
    back = run_async(connected_arb.get_body("plan_node", "n1"))
    assert back.body_text == "v2"


def test_get_body_missing_returns_none(connected_arb, run_async):
    assert run_async(connected_arb.get_body("plan_node", "ghost")) is None


def test_body_owner_type_scopes_lookup(connected_arb, run_async):
    run_async(connected_arb.set_body("plan_node", "x", "node-body"))
    run_async(connected_arb.set_body("message", "x", "msg-body"))
    assert run_async(connected_arb.get_body("plan_node", "x")).body_text == "node-body"
    assert run_async(connected_arb.get_body("message", "x")).body_text == "msg-body"
