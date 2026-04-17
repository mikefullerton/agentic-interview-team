"""Write-time cycle detection for node_dependency edges."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_DB = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db"
sys.path.insert(0, str(SCRIPTS_DB))

import cycle_check  # noqa: E402


def _three_nodes(make_roadmap, make_node):
    rm = make_roadmap()
    make_node("a", rm, position=1.0)
    make_node("b", rm, position=2.0)
    make_node("c", rm, position=3.0)
    return rm


def test_self_edge_is_cycle(conn, make_roadmap, make_node, now):
    _three_nodes(make_roadmap, make_node)
    assert cycle_check.would_create_cycle(conn, "a", "a") is True
    with pytest.raises(cycle_check.CycleError):
        cycle_check.insert_dependency(conn, "a", "a", now)


def test_direct_two_cycle_rejected(conn, make_roadmap, make_node, now):
    _three_nodes(make_roadmap, make_node)
    # a depends on b is fine.
    cycle_check.insert_dependency(conn, "a", "b", now)
    # b depends on a would create a 2-cycle.
    assert cycle_check.would_create_cycle(conn, "b", "a") is True
    with pytest.raises(cycle_check.CycleError):
        cycle_check.insert_dependency(conn, "b", "a", now)


def test_indirect_three_cycle_rejected(conn, make_roadmap, make_node, now):
    _three_nodes(make_roadmap, make_node)
    # a depends on b, b depends on c
    cycle_check.insert_dependency(conn, "a", "b", now)
    cycle_check.insert_dependency(conn, "b", "c", now)
    # c depends on a would close the 3-cycle.
    assert cycle_check.would_create_cycle(conn, "c", "a") is True
    with pytest.raises(cycle_check.CycleError):
        cycle_check.insert_dependency(conn, "c", "a", now)


def test_unrelated_dependency_is_fine(conn, make_roadmap, make_node, now):
    _three_nodes(make_roadmap, make_node)
    cycle_check.insert_dependency(conn, "a", "b", now)
    # c depends on b is unrelated to the a→b edge, no cycle.
    assert cycle_check.would_create_cycle(conn, "c", "b") is False
    cycle_check.insert_dependency(conn, "c", "b", now)


def test_diamond_is_not_a_cycle(conn, make_roadmap, make_node, now):
    """A DAG diamond — a depends on b and c; b and c both depend on d —
    is not a cycle. Both paths converge but no back-edge exists."""
    rm = make_roadmap()
    for n in ("a", "b", "c", "d"):
        make_node(n, rm, position={"a": 1, "b": 2, "c": 3, "d": 4}[n])
    cycle_check.insert_dependency(conn, "a", "b", now)
    cycle_check.insert_dependency(conn, "a", "c", now)
    cycle_check.insert_dependency(conn, "b", "d", now)
    # No cycle if we make c also depend on d.
    assert cycle_check.would_create_cycle(conn, "c", "d") is False
    cycle_check.insert_dependency(conn, "c", "d", now)


def test_cycle_check_survives_long_chain(conn, make_roadmap, make_node, now):
    """A chain n1 → n2 → ... → n10 is acyclic. Closing the chain (n10 → n1)
    creates a cycle."""
    rm = make_roadmap()
    for i in range(1, 11):
        make_node(f"n{i}", rm, position=float(i))
    for i in range(1, 10):
        cycle_check.insert_dependency(conn, f"n{i}", f"n{i+1}", now)

    assert cycle_check.would_create_cycle(conn, "n10", "n1") is True
    with pytest.raises(cycle_check.CycleError):
        cycle_check.insert_dependency(conn, "n10", "n1", now)


def test_rejected_insert_leaves_no_row(conn, make_roadmap, make_node, now):
    """A rejected dependency does not leak a partial row into node_dependency."""
    _three_nodes(make_roadmap, make_node)
    cycle_check.insert_dependency(conn, "a", "b", now)
    with pytest.raises(cycle_check.CycleError):
        cycle_check.insert_dependency(conn, "b", "a", now)
    # Only the a→b edge exists.
    rows = conn.execute(
        "SELECT node_id, depends_on_id FROM node_dependency ORDER BY node_id"
    ).fetchall()
    assert rows == [("a", "b")]
