"""DAG projection: follow node_dependency only.

Kahn's algorithm in Python over the node_dependency table. Topological
order must exist (no cycle) and satisfy every prerequisite edge.

Shape (matches tree test but now with dependencies):

    source-control  →  (no deps)
    logistics       →  depends on source-control
    editor          →  depends on logistics
    preview         →  depends on editor
    app             →  depends on preview
    root            →  depends on app, logistics

Plus a second roadmap exercising a diamond: a → b, a → c, b → d, c → d.
"""
from __future__ import annotations


def _build_linear_roadmap(seed_roadmap, seed_node, add_edge):
    rm = seed_roadmap(roadmap_id="rm-linear")
    seed_node("root",           rm, position=1.0, node_kind="compound")
    seed_node("logistics",      rm, parent_id="root",      position=1.0, node_kind="compound")
    seed_node("source-control", rm, parent_id="logistics", position=1.0)
    seed_node("app",            rm, parent_id="root",      position=2.0, node_kind="compound")
    seed_node("editor",         rm, parent_id="app",       position=1.0)
    seed_node("preview",        rm, parent_id="app",       position=2.0)
    add_edge("logistics", "source-control")
    add_edge("editor",    "logistics")
    add_edge("preview",   "editor")
    add_edge("app",       "preview")
    add_edge("root",      "app")
    add_edge("root",      "logistics")
    return rm


def _build_diamond_roadmap(seed_roadmap, seed_node, add_edge):
    rm = seed_roadmap(roadmap_id="rm-diamond")
    for nid, pos in (("a", 1.0), ("b", 2.0), ("c", 3.0), ("d", 4.0)):
        seed_node(nid, rm, position=pos)
    add_edge("b", "a")
    add_edge("c", "a")
    add_edge("d", "b")
    add_edge("d", "c")
    return rm


def _topo_order(sqlite_conn, roadmap_id: str) -> list[str]:
    """Kahn's algorithm. Returns a valid topological order or [] if cyclic."""
    nodes = [r[0] for r in sqlite_conn.execute(
        "SELECT node_id FROM plan_node WHERE roadmap_id = ?", (roadmap_id,)
    ).fetchall()]
    node_set = set(nodes)
    edges = sqlite_conn.execute(
        "SELECT node_id, depends_on_id FROM node_dependency"
    ).fetchall()
    edges = [(n, d) for n, d in edges if n in node_set and d in node_set]

    in_degree = {n: 0 for n in nodes}
    out_edges: dict[str, list[str]] = {n: [] for n in nodes}
    for dependent, prereq in edges:
        in_degree[dependent] += 1
        out_edges[prereq].append(dependent)

    order: list[str] = []
    ready = sorted([n for n in nodes if in_degree[n] == 0])
    while ready:
        n = ready.pop(0)
        order.append(n)
        for succ in sorted(out_edges[n]):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                ready.append(succ)
        ready.sort()
    if len(order) != len(nodes):
        return []
    return order


def test_linear_dag_produces_total_ordering(
    sqlite_conn, seed_roadmap, seed_node, add_edge
):
    rm = _build_linear_roadmap(seed_roadmap, seed_node, add_edge)
    order = _topo_order(sqlite_conn, rm)
    assert set(order) == {
        "root", "logistics", "source-control", "app", "editor", "preview"
    }
    pos = {n: i for i, n in enumerate(order)}
    assert pos["source-control"] < pos["logistics"]
    assert pos["logistics"] < pos["editor"]
    assert pos["editor"] < pos["preview"]
    assert pos["preview"] < pos["app"]
    assert pos["app"] < pos["root"]
    assert pos["logistics"] < pos["root"]


def test_diamond_dag_orders_shared_ancestor_first(
    sqlite_conn, seed_roadmap, seed_node, add_edge
):
    rm = _build_diamond_roadmap(seed_roadmap, seed_node, add_edge)
    order = _topo_order(sqlite_conn, rm)
    assert set(order) == {"a", "b", "c", "d"}
    pos = {n: i for i, n in enumerate(order)}
    assert pos["a"] < pos["b"]
    assert pos["a"] < pos["c"]
    assert pos["b"] < pos["d"]
    assert pos["c"] < pos["d"]


def test_ready_query_picks_nodes_with_all_deps_done(
    sqlite_conn, seed_roadmap, seed_node, add_edge, iso_now
):
    """Executor-style ready query: pick nodes whose prereqs all emitted 'done'."""
    rm = _build_linear_roadmap(seed_roadmap, seed_node, add_edge)
    sqlite_conn.execute(
        "INSERT INTO node_state_event (node_id, event_type, actor, event_date) "
        "VALUES ('source-control', 'done', 'executor', ?)", (iso_now,)
    )
    sqlite_conn.commit()

    ready_rows = sqlite_conn.execute("""
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
    ready = {r[0] for r in ready_rows}

    assert "logistics" in ready
    assert "editor" not in ready
    assert "source-control" not in ready


def test_topo_sort_is_stable_for_independent_nodes(
    sqlite_conn, seed_roadmap, seed_node
):
    """Nodes with no dependency relationship emerge in alphabetical order
    (our implementation sorts ready nodes). Regression guard if someone
    changes the ordering convention."""
    rm = seed_roadmap(roadmap_id="rm-indep")
    for nid, pos in (("zed", 1.0), ("alpha", 2.0), ("middle", 3.0)):
        seed_node(nid, rm, position=pos)
    order = _topo_order(sqlite_conn, rm)
    assert order == ["alpha", "middle", "zed"]
