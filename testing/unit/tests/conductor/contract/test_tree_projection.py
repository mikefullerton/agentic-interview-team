"""Tree projection: follow parent_id only.

Shape used here (mirrors docs/planning/2026-04-17-atp-roadmap-design.md):

    root
    ├── logistics
    │   └── source-control
    └── app
        ├── editor
        └── preview
"""
from __future__ import annotations

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


def _build_tree(seed_roadmap, seed_node):
    rm = seed_roadmap()
    seed_node("root",           rm, parent_id=None,        position=1.0, node_kind="compound")
    seed_node("logistics",      rm, parent_id="root",      position=1.0, node_kind="compound")
    seed_node("source-control", rm, parent_id="logistics", position=1.0)
    seed_node("app",            rm, parent_id="root",      position=2.0, node_kind="compound")
    seed_node("editor",         rm, parent_id="app",       position=1.0)
    seed_node("preview",        rm, parent_id="app",       position=2.0)
    return rm


def test_tree_cte_returns_every_node(sqlite_conn, seed_roadmap, seed_node):
    rm = _build_tree(seed_roadmap, seed_node)
    rows = sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()
    assert {r[0] for r in rows} == {
        "root", "logistics", "source-control", "app", "editor", "preview"
    }


def test_tree_cte_reports_correct_depth(sqlite_conn, seed_roadmap, seed_node):
    rm = _build_tree(seed_roadmap, seed_node)
    depth = {r[0]: r[2] for r in sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    assert depth == {
        "root": 0,
        "logistics": 1,
        "app": 1,
        "source-control": 2,
        "editor": 2,
        "preview": 2,
    }


def test_tree_cte_builds_slash_path_from_hierarchy(sqlite_conn, seed_roadmap, seed_node):
    rm = _build_tree(seed_roadmap, seed_node)
    paths = {r[0]: r[3] for r in sqlite_conn.execute(TREE_CTE, (rm, rm)).fetchall()}
    assert paths["source-control"] == "root/logistics/source-control"
    assert paths["editor"] == "root/app/editor"
    assert paths["preview"] == "root/app/preview"


def test_tree_cte_ignores_other_roadmaps(sqlite_conn, seed_roadmap, seed_node):
    rm_a = seed_roadmap(roadmap_id="rm-a")
    rm_b = seed_roadmap(roadmap_id="rm-b")
    seed_node("a-root", rm_a, position=1.0, node_kind="compound")
    seed_node("b-root", rm_b, position=1.0, node_kind="compound")
    rows_a = sqlite_conn.execute(TREE_CTE, (rm_a, rm_a)).fetchall()
    assert [r[0] for r in rows_a] == ["a-root"]
