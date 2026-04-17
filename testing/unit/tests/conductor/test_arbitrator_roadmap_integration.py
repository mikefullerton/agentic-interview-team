"""End-to-end: roadmap + session + cross-stream attribution.

Exercises the whole flow a real atp session would use:
  1. Create a roadmap with a small tree of plan nodes.
  2. Wire DAG dependencies.
  3. Open a session anchored to a node.
  4. Create messages / results / events / tasks attributed to that node.
  5. Record node state transitions.
  6. Query the cross-stream filter to confirm everything lines up.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import (
    BodyFormat,
    NodeKind,
    NodeStateEventType,
)


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "integration.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def _build_toy_roadmap(arb, run_async):
    """Returns (rm, dict of node_id → title) for the toy roadmap."""
    rm = run_async(arb.create_roadmap("Markdown Editor"))
    root = run_async(arb.create_plan_node(
        rm.roadmap_id, "root", NodeKind.COMPOUND,
        node_id="n-root", position=1.0,
    ))
    logistics = run_async(arb.create_plan_node(
        rm.roadmap_id, "logistics", NodeKind.COMPOUND,
        parent_id=root.node_id, node_id="n-logistics", position=1.0,
    ))
    source_control = run_async(arb.create_plan_node(
        rm.roadmap_id, "source-control", NodeKind.PRIMITIVE,
        parent_id=logistics.node_id, node_id="n-sc", position=1.0,
        specialist="development-process",
    ))
    app = run_async(arb.create_plan_node(
        rm.roadmap_id, "app", NodeKind.COMPOUND,
        parent_id=root.node_id, node_id="n-app", position=2.0,
    ))
    editor = run_async(arb.create_plan_node(
        rm.roadmap_id, "editor", NodeKind.PRIMITIVE,
        parent_id=app.node_id, node_id="n-editor", position=1.0,
        specialist="platform-ios-apple",
    ))
    preview = run_async(arb.create_plan_node(
        rm.roadmap_id, "preview", NodeKind.PRIMITIVE,
        parent_id=app.node_id, node_id="n-preview", position=2.0,
    ))

    # DAG: logistics first, then editor, then preview, root at the end.
    run_async(arb.add_dependency(logistics.node_id, source_control.node_id))
    run_async(arb.add_dependency(editor.node_id, logistics.node_id))
    run_async(arb.add_dependency(preview.node_id, editor.node_id))
    run_async(arb.add_dependency(app.node_id, preview.node_id))
    run_async(arb.add_dependency(root.node_id, app.node_id))
    return rm


def test_full_roadmap_and_cross_stream(arb, run_async):
    rm = _build_toy_roadmap(arb, run_async)

    # Verify the tree projection (list all nodes).
    nodes = run_async(arb.list_plan_nodes(rm.roadmap_id))
    assert {n.title for n in nodes} == {
        "root", "logistics", "source-control", "app", "editor", "preview"
    }

    # Verify direct children of app.
    children = run_async(arb.list_plan_nodes_by_parent(rm.roadmap_id, "n-app"))
    assert {c.title for c in children} == {"editor", "preview"}

    # Open a session anchored at the editor node.
    sid = uuid4()
    run_async(arb.open_session(sid, "executor-team"))

    # Log some activity against the editor node: a state, messages, events,
    # a result, and a lifecycle event.
    run_async(arb.push_state(
        sid, "executor-team", "dispatching", parent_node_id=None,
        plan_node_id="n-editor",
    ))
    run_async(arb.create_message(
        sid, "executor-team", "out", "notification",
        "Starting editor build", plan_node_id="n-editor",
    ))
    run_async(arb.emit_event(
        sid, "executor-team", "tool-use", {"tool": "bash"},
        plan_node_id="n-editor",
    ))
    run_async(arb.create_result(
        sid, "executor-team", "platform-ios-apple",
        passed=True, summary={"lines_changed": 42},
        plan_node_id="n-editor",
    ))
    run_async(arb.record_node_state_event(
        "n-editor", NodeStateEventType.RUNNING,
        actor="executor", session_id=sid,
    ))
    run_async(arb.record_node_state_event(
        "n-editor", NodeStateEventType.DONE,
        actor="executor", session_id=sid,
    ))

    # Latest state for editor is DONE.
    latest = run_async(arb.latest_node_state("n-editor"))
    assert latest.event_type == NodeStateEventType.DONE

    # Per-node observability: count stream rows tagged to editor.
    msgs = run_async(arb.list_messages(sid))
    msgs_for_editor = [m for m in msgs if m.plan_node_id == "n-editor"]
    assert len(msgs_for_editor) == 1

    events = run_async(arb.list_events(sid))
    events_for_editor = [e for e in events if e.plan_node_id == "n-editor"]
    assert len(events_for_editor) == 1

    results = run_async(arb.list_results(sid))
    results_for_editor = [r for r in results if r.plan_node_id == "n-editor"]
    assert len(results_for_editor) == 1


def test_body_side_table_for_node_description(arb, run_async):
    rm = _build_toy_roadmap(arb, run_async)
    # Attach a markdown description to the editor node.
    run_async(arb.set_body(
        "plan_node", "n-editor",
        "# Markdown Editor Window\n\nHosts text editing + preview.",
        body_format=BodyFormat.MARKDOWN,
    ))
    body = run_async(arb.get_body("plan_node", "n-editor"))
    assert body is not None
    assert "Markdown Editor Window" in body.body_text
    assert body.body_format == BodyFormat.MARKDOWN


def test_dag_dependencies_enforce_ordering_queries(arb, run_async):
    rm = _build_toy_roadmap(arb, run_async)
    # logistics depends on source-control; editor depends on logistics.
    editor_deps = run_async(arb.list_dependencies_of("n-editor"))
    assert [d.depends_on_id for d in editor_deps] == ["n-logistics"]

    logistics_deps = run_async(arb.list_dependencies_of("n-logistics"))
    assert [d.depends_on_id for d in logistics_deps] == ["n-sc"]

    # source-control has no deps.
    sc_deps = run_async(arb.list_dependencies_of("n-sc"))
    assert sc_deps == []
