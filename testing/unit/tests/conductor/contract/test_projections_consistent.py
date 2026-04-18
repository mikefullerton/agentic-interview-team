"""Tree and DAG projections are two views of the same underlying plan_node rows.

Neither projection may add or lose a node. If they diverge, some node is
either missing a parent_id (tree orphan) or excluded from the roadmap
filter incorrectly.
"""
from __future__ import annotations


TREE_CTE = """
WITH RECURSIVE tree(node_id) AS (
    SELECT node_id FROM plan_node WHERE roadmap_id = ? AND parent_id IS NULL
    UNION ALL
    SELECT pn.node_id FROM plan_node pn
    JOIN tree t ON pn.parent_id = t.node_id
    WHERE pn.roadmap_id = ?
)
SELECT node_id FROM tree;
"""


def _build(seed_roadmap, seed_node, add_edge):
    rm = seed_roadmap(roadmap_id="rm-shared")
    seed_node("root", rm, position=1.0, node_kind="compound")
    seed_node("a",    rm, parent_id="root", position=1.0, node_kind="compound")
    seed_node("b",    rm, parent_id="root", position=2.0)
    seed_node("c",    rm, parent_id="a",    position=1.0)
    seed_node("d",    rm, parent_id="a",    position=2.0)
    add_edge("a", "b")
    add_edge("c", "d")
    return rm


def test_tree_walk_and_all_nodes_query_return_same_set(
    sqlite_conn, seed_roadmap, seed_node, add_edge
):
    rm = _build(seed_roadmap, seed_node, add_edge)
    tree_ids = {r[0] for r in sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    all_ids = {r[0] for r in sqlite_conn.execute(
        "SELECT node_id FROM plan_node WHERE roadmap_id = ?", (rm,)
    ).fetchall()}
    assert tree_ids == all_ids


def test_dependency_nodes_are_subset_of_tree_nodes(
    sqlite_conn, seed_roadmap, seed_node, add_edge
):
    """Every endpoint of a node_dependency edge must be a real plan_node in
    the roadmap. No 'phantom' DAG-only nodes."""
    rm = _build(seed_roadmap, seed_node, add_edge)
    tree_ids = {r[0] for r in sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    dep_ids = set()
    for dependent, prereq in sqlite_conn.execute(
        "SELECT node_id, depends_on_id FROM node_dependency"
    ).fetchall():
        dep_ids.add(dependent)
        dep_ids.add(prereq)
    assert dep_ids <= tree_ids


def test_tree_has_no_orphans_outside_roots(
    sqlite_conn, seed_roadmap, seed_node
):
    """Every non-root node must appear as a descendant of some root under
    its roadmap — no orphan subtrees."""
    rm = seed_roadmap(roadmap_id="rm-orphan-check")
    seed_node("r1", rm, position=1.0, node_kind="compound")
    seed_node("r2", rm, position=2.0, node_kind="compound")
    seed_node("child-r1", rm, parent_id="r1", position=1.0)
    seed_node("child-r2", rm, parent_id="r2", position=1.0)

    tree_ids = {r[0] for r in sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    all_ids = {r[0] for r in sqlite_conn.execute(
        "SELECT node_id FROM plan_node WHERE roadmap_id = ?", (rm,)
    ).fetchall()}
    assert tree_ids == all_ids
