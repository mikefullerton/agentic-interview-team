#!/usr/bin/env python3
"""Cycle detection for node_dependency inserts.

Schema-v3 does not enforce DAG acyclicity structurally — SQLite can't. This
helper does write-time detection: before inserting a dependency edge
(dependent → prerequisite), walk the prerequisite's dependency chain and
reject if we ever reach the dependent.

Two entry points:

  would_create_cycle(conn, dependent, prerequisite) -> bool
  insert_dependency(conn, dependent, prerequisite, creation_date) -> None
      (raises CycleError if the edge would create a cycle)
"""
from __future__ import annotations

import sqlite3
from typing import Iterable


class CycleError(ValueError):
    """Raised when a proposed node_dependency edge would create a cycle."""


def _prerequisites_of(conn: sqlite3.Connection, node_id: str) -> Iterable[str]:
    """Direct prerequisites of node_id (one hop along depends_on)."""
    rows = conn.execute(
        "SELECT depends_on_id FROM node_dependency WHERE node_id = ?",
        (node_id,),
    ).fetchall()
    return [r[0] for r in rows]


def would_create_cycle(
    conn: sqlite3.Connection, dependent: str, prerequisite: str
) -> bool:
    """True if adding (dependent depends_on prerequisite) creates a cycle.

    Self-edge is always a cycle. Otherwise: walk forward from prerequisite
    along existing depends_on edges; if we ever reach dependent, the new
    edge would close a cycle.
    """
    if dependent == prerequisite:
        return True

    # BFS from prerequisite outward through its own prerequisites.
    visited = {prerequisite}
    frontier = [prerequisite]
    while frontier:
        current = frontier.pop()
        for next_node in _prerequisites_of(conn, current):
            if next_node == dependent:
                return True
            if next_node not in visited:
                visited.add(next_node)
                frontier.append(next_node)
    return False


def insert_dependency(
    conn: sqlite3.Connection,
    dependent: str,
    prerequisite: str,
    creation_date: str,
) -> None:
    """Insert a node_dependency edge, raising CycleError if it would cycle."""
    if would_create_cycle(conn, dependent, prerequisite):
        raise CycleError(
            f"adding ({dependent} depends_on {prerequisite}) would create a cycle"
        )
    conn.execute(
        "INSERT INTO node_dependency (node_id, depends_on_id, creation_date) "
        "VALUES (?, ?, ?)",
        (dependent, prerequisite, creation_date),
    )
