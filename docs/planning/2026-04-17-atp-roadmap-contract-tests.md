# atp Roadmap — Arbitrator Contract Tests Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin behavior of the arbitrator resources introduced by PRs #10-15 — the roadmap graph (`roadmap`, `plan_node`, `node_dependency`, `node_state_event`), the `body` side-table, and the `plan_node_id` join key added to every stream table — with contract tests keyed to verification items 2-4 of `docs/planning/2026-04-17-atp-roadmap-design.md`.

**Architecture:** Contract tests pin current behavior of the **live conductor schema** at `plugins/dev-team/services/conductor/arbitrator/backends/schema.sql` and the Python `Arbitrator` facade at `plugins/dev-team/services/conductor/arbitrator/api.py`. Tests live under a new `testing/unit/tests/conductor/contract/` subdirectory next to the existing roadmap tests, reuse the parent `conftest.py` fixtures (`arb_factory`, `run_async`, `session_id`), and add a local `conftest.py` for raw-SQL fixtures (the parent doesn't provide them). Each task produces one self-contained test file and commits independently.

**Tech Stack:** Python 3.10+, pytest, sqlite3, asyncio (via the `run_async` helper in the parent conftest), the `Arbitrator` API and `SqliteBackend`.

---

## Scope Notes

**In scope — contract tests for the LIVE conductor schema:**
- Roadmap graph tables: `roadmap`, `plan_node`, `node_dependency`, `node_state_event`.
- `body` side-table.
- `plan_node_id` join key on every stream table that currently carries it: `state`, `message`, `gate`, `result`, `finding`, `event`, `task`, `request`, `decision`.
- `session.roadmap_id` column (PR #11).
- `Arbitrator` facade methods added/changed in PRs #10-15.
- Verification items 2 (schema conformance linter), 3 (tree/DAG round-trip), 4 (cross-stream filter) from the design doc.

**Out of scope — defer to a follow-up plan:**
- `dispatch` and `attempt` tables. These exist in the **reference** schema at `plugins/dev-team/scripts/db/schema-v3.sql` and are exercised by `testing/unit/tests/atp/db/test_cross_stream.py`, but the live conductor schema has not yet added them. When the live schema gains them, extend the cross-stream filter task below and add dispatch/attempt round-trip tests.
- Markdown exporter (`roadmap_export.py`) — already has 14 tests; no contract gap.

**Test location correction:** The request referenced `tests/arbitrator/`. The existing CLI-subprocess contract tests at `testing/unit/tests/arbitrator/` cover the pre-conductor `arbitrator.py` CLI, which does NOT expose the new roadmap resources. Roadmap resources are Python-API only, so these contract tests go under `testing/unit/tests/conductor/contract/`.

## Existing Coverage (do not duplicate)

| Resource | File | What it pins |
|---|---|---|
| Raw schema: roadmap/plan_node/node_dependency/node_state_event/body exist, FKs, unique, append-only log, body composite PK | `testing/unit/tests/conductor/test_arbitrator_roadmap_schema.py` | Table shape |
| Arbitrator API: create/list roadmap + plan_node, deps, 3 cycle cases, 4 lifecycle event types, body get/set/upsert/owner-type scoping | `testing/unit/tests/conductor/test_arbitrator_roadmap_api.py` | Facade CRUD |
| Raw SQL: `plan_node_id` nullable default, FK rejects unknown, works on 6 streams, 3-stream UNION, legacy insert patterns | `testing/unit/tests/conductor/test_arbitrator_plan_node_id.py` | Join-key shape |
| Facade wiring of `plan_node_id` through 7 create methods; omitting keeps old behavior | `testing/unit/tests/conductor/test_arbitrator_plan_node_wiring.py` | Facade wiring |
| Round-trip for every resource via Arbitrator API | `testing/unit/tests/conductor/test_arbitrator_schema_roundtrip.py` | Full round-trip |
| Reference schema-v3.sql (tree CTE, DAG topo, cross-stream over 7+dispatch/attempt, cycle detect, crash resume) | `testing/unit/tests/atp/db/test_*.py` | Reference schema |

## File Structure

```
testing/unit/tests/conductor/contract/
├── __init__.py                           # empty; makes the dir a package
├── conftest.py                           # raw sqlite_conn fixture against the live schema; helpers
├── test_schema_conforms.py               # Task 2 — verification item 2
├── test_tree_projection.py               # Task 3 — verification item 3 (tree half)
├── test_dag_projection.py                # Task 4 — verification item 3 (DAG half)
├── test_projections_consistent.py        # Task 5 — tree ∪ DAG same node set
├── test_cross_stream_filter.py           # Task 6 — verification item 4, 9 streams
├── test_node_state_event_lifecycle.py    # Task 7 — all 6 event types + superseded
└── test_body_owner_types.py              # Task 8 — body across the owner_types PR #13 added
```

Eight tasks total. Each task: write file, run the new tests only, commit. Tests are **locks, not red-green cycles** — they should pass on first run because the behavior already exists. A failing first run means the schema drifted or the fixture is wrong; investigate before changing the test.

---

## Task 1: Contract test package setup

**Files:**
- Create: `testing/unit/tests/conductor/contract/__init__.py`
- Create: `testing/unit/tests/conductor/contract/conftest.py`

- [ ] **Step 1: Create the package marker**

`testing/unit/tests/conductor/contract/__init__.py`:

```python
```

(Empty file — just marks the directory as a package so pytest can discover it.)

- [ ] **Step 2: Create the contract conftest**

`testing/unit/tests/conductor/contract/conftest.py`:

```python
"""Fixtures for roadmap contract tests.

The parent conductor/conftest.py supplies arb_factory, run_async, session_id,
and backend_factory. This module adds raw-sqlite fixtures that load the
LIVE conductor schema (not the reference schema-v3.sql that atp/db/ uses).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

LIVE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4]
    / "plugins" / "dev-team" / "services" / "conductor"
    / "arbitrator" / "backends" / "schema.sql"
)


@pytest.fixture
def live_schema_sql() -> str:
    return LIVE_SCHEMA_PATH.read_text()


@pytest.fixture
def sqlite_conn(live_schema_sql):
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(live_schema_sql)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@pytest.fixture
def seed_session(sqlite_conn, iso_now):
    """Insert one session row and return its id. No roadmap linkage by default."""
    def _factory(session_id: str = "sess-c", roadmap_id: str | None = None) -> str:
        sqlite_conn.execute(
            "INSERT INTO session "
            "(session_id, initial_team_id, status, roadmap_id, creation_date) "
            "VALUES (?, 't1', 'open', ?, ?)",
            (session_id, roadmap_id, iso_now),
        )
        sqlite_conn.commit()
        return session_id
    return _factory


@pytest.fixture
def seed_roadmap(sqlite_conn, iso_now):
    """Insert a roadmap and return its id."""
    def _factory(roadmap_id: str = "rm-c", title: str = "Contract Roadmap") -> str:
        sqlite_conn.execute(
            "INSERT INTO roadmap (roadmap_id, title, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?)",
            (roadmap_id, title, iso_now, iso_now),
        )
        sqlite_conn.commit()
        return roadmap_id
    return _factory


@pytest.fixture
def seed_node(sqlite_conn, iso_now):
    """Insert a plan_node and return its id."""
    def _factory(
        node_id: str,
        roadmap_id: str,
        *,
        parent_id: str | None = None,
        position: float = 1.0,
        node_kind: str = "primitive",
        title: str | None = None,
    ) -> str:
        sqlite_conn.execute(
            "INSERT INTO plan_node (node_id, roadmap_id, parent_id, position, "
            "node_kind, title, creation_date, modification_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (node_id, roadmap_id, parent_id, position, node_kind,
             title or node_id, iso_now, iso_now),
        )
        sqlite_conn.commit()
        return node_id
    return _factory


@pytest.fixture
def add_edge(sqlite_conn, iso_now):
    """Insert a node_dependency edge."""
    def _factory(node_id: str, depends_on_id: str) -> None:
        sqlite_conn.execute(
            "INSERT INTO node_dependency (node_id, depends_on_id, creation_date) "
            "VALUES (?, ?, ?)",
            (node_id, depends_on_id, iso_now),
        )
        sqlite_conn.commit()
    return _factory
```

- [ ] **Step 3: Verify the package loads and the schema is readable**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/ --collect-only -q`
Expected: `0 tests collected` with no import errors.

- [ ] **Step 4: Commit**

```bash
git add testing/unit/tests/conductor/contract/__init__.py \
        testing/unit/tests/conductor/contract/conftest.py
git commit -m "test(contract): scaffold roadmap arbitrator contract test package"
```

---

## Task 2: Schema conformance linter contract (verification item 2)

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_schema_conforms.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_schema_conforms.py`:

```python
"""The LIVE conductor schema must pass every check in schema_lint.py.

If this breaks, either the schema drifted from .claude/rules/db-schema-design.md
or a new rule was added. Investigate the named violation, not this test.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
LINT_SCRIPT = REPO_ROOT / "plugins" / "dev-team" / "scripts" / "db" / "schema_lint.py"


def _load_linter():
    sys.path.insert(0, str(LINT_SCRIPT.parent))
    try:
        import schema_lint
    finally:
        sys.path.pop(0)
    return schema_lint


def test_live_schema_produces_no_violations(live_schema_sql):
    linter = _load_linter()
    violations = linter.lint(live_schema_sql)
    assert violations == [], (
        "live conductor schema violates db-schema-design.md:\n  "
        + "\n  ".join(violations)
    )


def test_all_five_checks_run(live_schema_sql):
    """The linter exposes five named checks; every one must actually run."""
    linter = _load_linter()
    names = [name for name, _fn in linter.CHECKS]
    assert names == [
        "no *_at date naming",
        "no blob columns in primary tables",
        "entity tables have creation_date",
        "plan_node_id join key present",
        "body side-table shape",
    ]


def test_linter_catches_injected_violation(live_schema_sql):
    """Sanity: if we deliberately inject a *_at column, the linter flags it."""
    linter = _load_linter()
    mutated = live_schema_sql + "\nCREATE TABLE _probe (probe_id TEXT PRIMARY KEY, probe_at TEXT);\n"
    violations = linter.lint(mutated)
    assert any("probe_at" in v for v in violations), (
        f"linter did not catch injected *_at column; got: {violations}"
    )
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_schema_conforms.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_schema_conforms.py
git commit -m "test(contract): live schema passes schema_lint (verification item 2)"
```

---

## Task 3: Tree projection via recursive CTE (verification item 3, tree half)

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_tree_projection.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_tree_projection.py`:

```python
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
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_tree_projection.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_tree_projection.py
git commit -m "test(contract): tree projection via recursive CTE (verification item 3)"
```

---

## Task 4: DAG projection via topological sort (verification item 3, DAG half)

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_dag_projection.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_dag_projection.py`:

```python
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
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_dag_projection.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_dag_projection.py
git commit -m "test(contract): DAG projection + topological sort (verification item 3)"
```

---

## Task 5: Tree and DAG projections cover the same node set

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_projections_consistent.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_projections_consistent.py`:

```python
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
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_projections_consistent.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_projections_consistent.py
git commit -m "test(contract): tree and DAG projections cover the same node set"
```

---

## Task 6: Cross-stream filter over every stream carrying plan_node_id (verification item 4)

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_cross_stream_filter.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_cross_stream_filter.py`:

```python
"""Given rows across every stream tagged with plan_node_id='target', a single
UNION query returns them all. Streams covered (live conductor schema):

    state, message, gate, result, finding, event, task, request, decision

Dispatch and attempt tables aren't in the live schema yet — see the Scope
Notes section of docs/planning/2026-04-17-atp-roadmap-contract-tests.md.
"""
from __future__ import annotations


def _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node):
    rm = seed_roadmap(roadmap_id="rm-x")
    seed_node("target", rm, position=1.0)
    seed_node("other",  rm, position=2.0)
    sess = seed_session(session_id="sess-x", roadmap_id=rm)
    return rm, sess


def test_cross_stream_union_returns_every_tagged_row(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    rm, sess = _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node)

    # One row per stream, all tagged with plan_node_id='target'.
    sqlite_conn.execute(
        "INSERT INTO state (node_id, session_id, team_id, plan_node_id, "
        "state_name, status, entry_date) "
        "VALUES ('st1', ?, 't1', 'target', 's', 'active', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "direction, type, creation_date) "
        "VALUES ('m1', ?, 't1', 'target', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO gate (gate_id, session_id, team_id, plan_node_id, category, "
        "options_json, creation_date) "
        "VALUES ('g1', ?, 't1', 'target', 'flow', '[]', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO result (result_id, session_id, team_id, plan_node_id, "
        "specialist_id, passed, summary_json, creation_date) "
        "VALUES ('res1', ?, 't1', 'target', 'sp', 1, '{}', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO finding (finding_id, result_id, plan_node_id, kind, "
        "severity, creation_date) "
        "VALUES ('f1', 'res1', 'target', 'note', 'info', ?)",
        (iso_now,),
    )
    sqlite_conn.execute(
        "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
        "sequence, kind, payload_json, event_date) "
        "VALUES ('e1', ?, 't1', 'target', 1, 'lifecycle', '{}', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO task (task_id, session_id, team_id, plan_node_id, kind, "
        "payload_json, status, scheduled_date) "
        "VALUES ('tk1', ?, 't1', 'target', 'dispatch', '{}', 'pending', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, kind, input_json, status, creation_date, timeout_date) "
        "VALUES ('rq1', ?, 't1', 't2', 'target', 'k', '{}', 'pending', ?, ?)",
        (sess, iso_now, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO decision (decision_id, session_id, team_id, plan_node_id, "
        "title, creation_date) "
        "VALUES ('d1', ?, 't1', 'target', 'use X', ?)",
        (sess, iso_now),
    )

    # Noise: 'other'-tagged + NULL rows that the filter must exclude.
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
        "direction, type, creation_date) "
        "VALUES ('m-other', ?, 't1', 'other', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.execute(
        "INSERT INTO message (message_id, session_id, team_id, direction, "
        "type, creation_date) "
        "VALUES ('m-null', ?, 't1', 'in', 'question', ?)",
        (sess, iso_now),
    )
    sqlite_conn.commit()

    query = """
        SELECT 'state'    AS stream, node_id     AS row_id FROM state    WHERE plan_node_id = :node
        UNION ALL
        SELECT 'message',  message_id  FROM message  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'gate',     gate_id     FROM gate     WHERE plan_node_id = :node
        UNION ALL
        SELECT 'result',   result_id   FROM result   WHERE plan_node_id = :node
        UNION ALL
        SELECT 'finding',  finding_id  FROM finding  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'event',    event_id    FROM event    WHERE plan_node_id = :node
        UNION ALL
        SELECT 'task',     task_id     FROM task     WHERE plan_node_id = :node
        UNION ALL
        SELECT 'request',  request_id  FROM request  WHERE plan_node_id = :node
        UNION ALL
        SELECT 'decision', decision_id FROM decision WHERE plan_node_id = :node
        ORDER BY stream, row_id
    """
    pairs = {(r[0], r[1]) for r in sqlite_conn.execute(query, {"node": "target"}).fetchall()}
    assert pairs == {
        ("state",    "st1"),
        ("message",  "m1"),
        ("gate",     "g1"),
        ("result",   "res1"),
        ("finding",  "f1"),
        ("event",    "e1"),
        ("task",     "tk1"),
        ("request",  "rq1"),
        ("decision", "d1"),
    }

    # 'other' filter returns only the one message tagged with 'other'.
    other = sqlite_conn.execute(query, {"node": "other"}).fetchall()
    assert other == [("message", "m-other")]


def test_per_stream_counts_via_group_by(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    rm, sess = _seed_target(sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node)

    for i in range(3):
        sqlite_conn.execute(
            "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
            "direction, type, creation_date) "
            "VALUES (?, ?, 't1', 'target', 'in', 'question', ?)",
            (f"m{i}", sess, iso_now),
        )
    for i in range(2):
        sqlite_conn.execute(
            "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
            "sequence, kind, payload_json, event_date) "
            "VALUES (?, ?, 't1', 'target', ?, 'lifecycle', '{}', ?)",
            (f"e{i}", sess, i + 1, iso_now),
        )
    sqlite_conn.execute(
        "INSERT INTO request (request_id, session_id, from_team, to_team, "
        "plan_node_id, kind, input_json, status, creation_date, timeout_date) "
        "VALUES ('rq1', ?, 't1', 't2', 'target', 'k', '{}', 'pending', ?, ?)",
        (sess, iso_now, iso_now),
    )
    sqlite_conn.commit()

    counts = dict(sqlite_conn.execute("""
        SELECT stream, COUNT(*) FROM (
            SELECT 'message' AS stream FROM message WHERE plan_node_id='target'
            UNION ALL
            SELECT 'event'             FROM event   WHERE plan_node_id='target'
            UNION ALL
            SELECT 'request'           FROM request WHERE plan_node_id='target'
        ) GROUP BY stream
    """).fetchall())
    assert counts == {"message": 3, "event": 2, "request": 1}


def test_unknown_plan_node_id_rejected_on_every_stream(
    sqlite_conn, iso_now, seed_session, seed_roadmap, seed_node
):
    """FK enforcement: no stream accepts an unknown plan_node_id."""
    import sqlite3
    seed_roadmap(roadmap_id="rm-fk")
    sess = seed_session(session_id="sess-fk")

    inserts = [
        ("state", "INSERT INTO state (node_id, session_id, team_id, plan_node_id, "
                  "state_name, status, entry_date) "
                  "VALUES ('st', ?, 't1', 'ghost', 's', 'active', ?)"),
        ("message", "INSERT INTO message (message_id, session_id, team_id, plan_node_id, "
                    "direction, type, creation_date) "
                    "VALUES ('m', ?, 't1', 'ghost', 'in', 'q', ?)"),
        ("event", "INSERT INTO event (event_id, session_id, team_id, plan_node_id, "
                  "sequence, kind, payload_json, event_date) "
                  "VALUES ('e', ?, 't1', 'ghost', 1, 'lifecycle', '{}', ?)"),
        ("task", "INSERT INTO task (task_id, session_id, team_id, plan_node_id, kind, "
                 "payload_json, status, scheduled_date) "
                 "VALUES ('tk', ?, 't1', 'ghost', 'dispatch', '{}', 'pending', ?)"),
        ("decision", "INSERT INTO decision (decision_id, session_id, team_id, plan_node_id, "
                     "title, creation_date) "
                     "VALUES ('d', ?, 't1', 'ghost', 'x', ?)"),
    ]

    for _table, sql in inserts:
        with __import__("pytest").raises(sqlite3.IntegrityError):
            sqlite_conn.execute(sql, (sess, iso_now))
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_cross_stream_filter.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_cross_stream_filter.py
git commit -m "test(contract): 9-stream cross-filter via plan_node_id (verification item 4)"
```

---

## Task 7: node_state_event lifecycle contract

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_node_state_event_lifecycle.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_node_state_event_lifecycle.py`:

```python
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
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_node_state_event_lifecycle.py -v`
Expected: 5 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_node_state_event_lifecycle.py
git commit -m "test(contract): node_state_event covers all 6 types + superseded reopen"
```

---

## Task 8: Body side-table contract across owner types

**Files:**
- Create: `testing/unit/tests/conductor/contract/test_body_owner_types.py`

- [ ] **Step 1: Write the contract**

`testing/unit/tests/conductor/contract/test_body_owner_types.py`:

```python
"""Body side-table contract — narrative content for every owner_type
the PR #13 migration introduced.

Existing test_arbitrator_roadmap_api.py covers plan_node + message. This
file adds finding, decision, and verifies the no-FK-enforcement contract
(body.owner_id is deliberately not FK'd to allow forward references and
inserts ahead of primary rows during schema evolution).
"""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import BodyFormat, NodeKind


@pytest.fixture
def connected_arb(tmp_path, run_async):
    arb = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(arb.start())
    yield arb
    run_async(arb.close())


def test_body_works_for_finding_owner(connected_arb, run_async, session_id):
    arb = connected_arb
    run_async(arb.open_session(session_id, initial_team_id="t"))
    result = run_async(arb.create_result(
        session_id=session_id, team_id="t", specialist_id="sp",
        passed=True, summary={},
    ))
    run_async(arb.create_finding(
        result_id=result.result_id, kind="note", severity="info",
        body="The narrative finding prose goes here.",
    ))
    # Look up body via side-table.
    rows = run_async(arb._storage.fetch_all("finding", where={"result_id": result.result_id}))
    body = run_async(arb.get_body("finding", rows[0]["finding_id"]))
    assert body is not None
    assert body.body_text == "The narrative finding prose goes here."


def test_body_works_for_decision_owner(connected_arb, run_async, session_id):
    arb = connected_arb
    run_async(arb.open_session(session_id, initial_team_id="pm"))
    decision = run_async(arb.create_decision_item(
        session_id=session_id, team_id="pm",
        title="Use SwiftUI", rationale="Better macOS+iOS story.",
        decided_by="user",
    ))
    body = run_async(arb.get_body("decision", decision["decision_id"]))
    assert body is not None
    assert body.body_text == "Better macOS+iOS story."


def test_body_works_for_plan_node_owner(connected_arb, run_async):
    arb = connected_arb
    rm = run_async(arb.create_roadmap("R"))
    node = run_async(arb.create_plan_node(
        rm.roadmap_id, "N", NodeKind.COMPOUND, node_id="n1",
    ))
    run_async(arb.set_body(
        "plan_node", node.node_id,
        "# Feature X\n\nDescribe the feature here.",
        body_format=BodyFormat.MARKDOWN,
    ))
    back = run_async(arb.get_body("plan_node", node.node_id))
    assert back.body_format == BodyFormat.MARKDOWN
    assert back.body_text.startswith("# Feature X")


def test_body_owner_id_is_not_fk_constrained(sqlite_conn, iso_now):
    """Body must accept an owner_id that no primary row currently uses.
    This is deliberate — body rows can precede their owner during bulk
    inserts — and changing it would break schema evolution."""
    sqlite_conn.execute(
        "INSERT INTO body (owner_type, owner_id, body_format, body_text, modification_date) "
        "VALUES ('plan_node', 'node-never-created', 'markdown', 'ghost body', ?)",
        (iso_now,),
    )
    sqlite_conn.commit()
    row = sqlite_conn.execute(
        "SELECT body_text FROM body "
        "WHERE owner_type='plan_node' AND owner_id='node-never-created'"
    ).fetchone()
    assert row[0] == "ghost body"


def test_body_is_upsert_across_calls(connected_arb, run_async):
    arb = connected_arb
    run_async(arb.set_body("plan_node", "nX", "v1"))
    run_async(arb.set_body("plan_node", "nX", "v2"))
    run_async(arb.set_body("plan_node", "nX", "v3"))
    back = run_async(arb.get_body("plan_node", "nX"))
    assert back.body_text == "v3"

    # Different owner_type with same owner_id must not collide.
    run_async(arb.set_body("finding", "nX", "finding-body"))
    assert run_async(arb.get_body("plan_node", "nX")).body_text == "v3"
    assert run_async(arb.get_body("finding",   "nX")).body_text == "finding-body"


def test_body_format_round_trips(connected_arb, run_async):
    arb = connected_arb
    run_async(arb.set_body("plan_node", "nA", "plain prose",
                           body_format=BodyFormat.PLAIN))
    run_async(arb.set_body("plan_node", "nB", "# md",
                           body_format=BodyFormat.MARKDOWN))
    run_async(arb.set_body("plan_node", "nC", "{\"k\": 1}",
                           body_format=BodyFormat.JSON))
    assert run_async(arb.get_body("plan_node", "nA")).body_format == BodyFormat.PLAIN
    assert run_async(arb.get_body("plan_node", "nB")).body_format == BodyFormat.MARKDOWN
    assert run_async(arb.get_body("plan_node", "nC")).body_format == BodyFormat.JSON
```

- [ ] **Step 2: Run it — expect PASS**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/test_body_owner_types.py -v`
Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/conductor/contract/test_body_owner_types.py
git commit -m "test(contract): body side-table across finding/decision/plan_node owners"
```

---

## Final verification

- [ ] **Step 1: Run the full contract suite**

Run: `python3 -m pytest testing/unit/tests/conductor/contract/ -v`
Expected: all tests pass (3 + 4 + 4 + 3 + 3 + 5 + 6 = 28 tests, plus the 3 schema-lint sanity checks = 31; minor drift is fine).

- [ ] **Step 2: Run the full conductor + atp test suites to confirm no regression**

Run: `python3 -m pytest testing/unit/tests/conductor/ testing/unit/tests/atp/ -q`
Expected: all pre-existing passing tests still pass; no new failures.

- [ ] **Step 3: Final summary commit if any follow-up tweaks were needed**

If everything passes cleanly in steps 1-2, no final commit is required — each task already committed its file. If any fixture or import issue surfaced, fix in place on the owning task's file and commit as `fix(contract): <one-line reason>`.

## Self-Review

- **Verification item 2 (schema conformance):** Task 2 asserts zero violations against the live schema plus a mutation-injection sanity check. Covered.
- **Verification item 3 (tree + DAG round-trip):** Task 3 covers the tree projection via a recursive CTE; Task 4 covers the DAG projection via topological sort including a diamond case; Task 5 asserts both projections cover the same node set. Covered.
- **Verification item 4 (cross-stream filter):** Task 6 plants one row per stream across all nine streams carrying `plan_node_id`, asserts the UNION returns exactly those nine rows, and excludes rows tagged with other nodes or with NULL. Covered.
- **Placeholder scan:** No TBDs, no "add validation," no "similar to Task N." Every test function has complete, runnable code.
- **Type consistency:** `NodeKind`, `NodeStateEventType`, `BodyFormat` names match `plugins/dev-team/services/conductor/arbitrator/models.py`. Fixture names (`sqlite_conn`, `seed_roadmap`, `seed_node`, `add_edge`, `iso_now`, `seed_session`) are consistent across every task. `run_async` and `session_id` come from the parent `conductor/conftest.py` — verified against its current definitions.
- **Deferred items flagged:** dispatch/attempt tables not in live schema; called out in Scope Notes so a follow-up plan can extend Task 6 when those tables land.
