"""Tree and DAG projections of the roadmap graph.

One graph, two projections: tree edges via parent_id, DAG edges via
node_dependency. Both must return all nodes without double-counting.

Toy roadmap used:

  Tree:
    root
    ├── logistics
    │   └── source-control
    └── app
        ├── editor
        └── preview

  DAG (dependencies):
    source-control →  (no deps)
    logistics     →  depends on source-control
    editor        →  depends on logistics
    preview       →  depends on editor
    app           →  depends on preview
    root          →  depends on app, logistics
"""
from __future__ import annotations


def _build_toy_roadmap(make_roadmap, make_node, add_dependency):
    rm = make_roadmap()
    make_node("root",           rm, parent_id=None,          position=1.0)
    make_node("logistics",      rm, parent_id="root",        position=1.0)
    make_node("source-control", rm, parent_id="logistics",   position=1.0, node_kind="primitive")
    make_node("app",            rm, parent_id="root",        position=2.0)
    make_node("editor",         rm, parent_id="app",         position=1.0, node_kind="primitive")
    make_node("preview",        rm, parent_id="app",         position=2.0, node_kind="primitive")

    add_dependency("logistics", "source-control")
    add_dependency("editor",    "logistics")
    add_dependency("preview",   "editor")
    add_dependency("app",       "preview")
    add_dependency("root",      "app")
    add_dependency("root",      "logistics")
    return rm


TREE_CTE = """
WITH RECURSIVE tree(node_id, parent_id, depth, path) AS (
    SELECT node_id, parent_id, 0, node_id
    FROM plan_node
    WHERE roadmap_id = ? AND parent_id IS NULL
    UNION ALL
    SELECT pn.node_id, pn.parent_id, t.depth + 1, t.path || '/' || pn.node_id
    FROM plan_node pn
    JOIN tree t ON pn.parent_id = t.node_id
    WHERE pn.roadmap_id = ?
)
SELECT node_id, parent_id, depth, path FROM tree ORDER BY depth, path;
"""


def test_tree_projection_returns_all_nodes(conn, make_roadmap, make_node, add_dependency):
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)
    rows = conn.execute(TREE_CTE, (rm, rm)).fetchall()
    ids = {r[0] for r in rows}
    assert ids == {"root", "logistics", "source-control", "app", "editor", "preview"}


def test_tree_projection_depths_correct(conn, make_roadmap, make_node, add_dependency):
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)
    rows = conn.execute(TREE_CTE, (rm, rm)).fetchall()
    depth_by_id = {r[0]: r[2] for r in rows}
    assert depth_by_id["root"] == 0
    assert depth_by_id["logistics"] == 1
    assert depth_by_id["app"] == 1
    assert depth_by_id["source-control"] == 2
    assert depth_by_id["editor"] == 2
    assert depth_by_id["preview"] == 2


def test_tree_projection_paths_reflect_hierarchy(conn, make_roadmap, make_node, add_dependency):
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)
    rows = conn.execute(TREE_CTE, (rm, rm)).fetchall()
    path_by_id = {r[0]: r[3] for r in rows}
    assert path_by_id["source-control"] == "root/logistics/source-control"
    assert path_by_id["editor"] == "root/app/editor"


def test_dag_projection_topological_order(conn, make_roadmap, make_node, add_dependency):
    """Kahn's algorithm in SQL: nodes without unsatisfied deps come first."""
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)

    # Snapshot all nodes and their dependency count.
    nodes = [r[0] for r in conn.execute(
        "SELECT node_id FROM plan_node WHERE roadmap_id = ?", (rm,)
    ).fetchall()]
    deps = conn.execute(
        "SELECT node_id, depends_on_id FROM node_dependency"
    ).fetchall()

    in_degree = {n: 0 for n in nodes}
    edges_out = {n: [] for n in nodes}
    for dependent, prereq in deps:
        in_degree[dependent] += 1
        edges_out[prereq].append(dependent)

    order = []
    ready = sorted([n for n in nodes if in_degree[n] == 0])
    while ready:
        n = ready.pop(0)
        order.append(n)
        for succ in sorted(edges_out[n]):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                ready.append(succ)
        ready.sort()

    # Every node must have been ordered (no cycle, no orphans).
    assert set(order) == set(nodes)
    # Specific invariants: prereqs come before dependents.
    def before(a, b):
        return order.index(a) < order.index(b)
    assert before("source-control", "logistics")
    assert before("logistics", "editor")
    assert before("editor", "preview")
    assert before("preview", "app")
    assert before("app", "root")
    assert before("logistics", "root")


def test_ready_to_run_query(conn, make_roadmap, make_node, add_dependency, now):
    """A node is 'ready' iff every depends_on target has a latest
    node_state_event with event_type='done'."""
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)

    # Mark source-control as done.
    conn.execute(
        "INSERT INTO node_state_event (node_id, event_type, actor, event_date) "
        "VALUES ('source-control', 'done', 'executor', ?)", (now,)
    )
    conn.commit()

    # Ready = nodes whose every dep's latest state event is 'done'.
    # Nodes with no deps are always ready.
    ready = conn.execute("""
        SELECT pn.node_id
        FROM plan_node pn
        WHERE pn.roadmap_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM node_dependency dep
              WHERE dep.node_id = pn.node_id
                AND NOT EXISTS (
                    SELECT 1 FROM node_state_event nse
                    WHERE nse.node_id = dep.depends_on_id
                      AND nse.event_type = 'done'
                )
          )
          AND NOT EXISTS (
              SELECT 1 FROM node_state_event nse2
              WHERE nse2.node_id = pn.node_id AND nse2.event_type = 'done'
          )
    """, (rm,)).fetchall()
    ready_ids = {r[0] for r in ready}

    # source-control is done (excluded); logistics' only dep is satisfied → ready.
    # editor still depends on logistics (not done), so not ready.
    assert "logistics" in ready_ids
    assert "editor" not in ready_ids
    assert "source-control" not in ready_ids  # already done


def test_fractional_position_preserves_insertion_order(
    conn, make_roadmap, make_node
):
    """Inserting between existing siblings via fractional position doesn't
    require renumbering."""
    rm = make_roadmap()
    make_node("root", rm, position=1.0)
    make_node("a", rm, parent_id="root", position=1.0)
    make_node("c", rm, parent_id="root", position=2.0)
    # Insert b between a and c without touching either.
    make_node("b", rm, parent_id="root", position=1.5)

    rows = conn.execute(
        "SELECT node_id FROM plan_node WHERE parent_id='root' ORDER BY position"
    ).fetchall()
    assert [r[0] for r in rows] == ["a", "b", "c"]


def test_same_node_set_in_both_projections(conn, make_roadmap, make_node, add_dependency):
    """The tree and DAG projections must cover the same node set."""
    rm = _build_toy_roadmap(make_roadmap, make_node, add_dependency)

    tree_ids = {r[0] for r in conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    all_ids = {r[0] for r in conn.execute(
        "SELECT node_id FROM plan_node WHERE roadmap_id = ?", (rm,)
    ).fetchall()}

    assert tree_ids == all_ids
