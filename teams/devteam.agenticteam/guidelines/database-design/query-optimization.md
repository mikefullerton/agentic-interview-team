---

id: 7FD21483-AD0B-407E-8A7F-103992403D36
title: "Query Optimization"
domain: agentic-cookbook://guidelines/implementing/data/query-optimization
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Rules for writing efficient SQLite and PostgreSQL queries, including query planner behavior, anti-patterns that cause full table scans, JSON query performance, subquery elimination, and CTE vs subquery tradeoffs."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - query-optimization
  - performance
  - query-planning
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/indexing.md
references:
  - https://sqlite.org/optoverview.html
  - https://www.sqlite.org/eqp.html
  - https://sqlite.org/queryplanner.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - performance-optimization
---

# Query Optimization

SQLite's query planner is good, but it cannot compensate for poorly structured queries. Write queries that cooperate with the planner: let indexes be used, minimize rows examined, and avoid patterns that force sequential scans or per-row subqueries.

## Reading EXPLAIN QUERY PLAN

Always check the query plan before shipping a new query that touches large tables.

```sql
EXPLAIN QUERY PLAN
SELECT o.id, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'active'
ORDER BY o.created_date DESC;
```

What each term means:
- `SCAN` — full table scan; investigate whether an index applies
- `SEARCH USING INDEX` — index-assisted lookup
- `SEARCH USING COVERING INDEX` — no table lookup needed (best outcome)
- `USE TEMP B-TREE FOR ORDER BY` — a sort step runs after the query; an index on the ORDER BY columns may eliminate it
- `AUTOMATIC INDEX` — SQLite built a temporary index at runtime; a permanent index would help
- `CORRELATED SCALAR SUBQUERY` — the subquery executes once per outer row; rewrite as a JOIN
- `MATERIALIZE` — subquery result stored in a temp table; may be avoidable
- `CO-ROUTINE` — subquery yields rows on demand; generally fine

Run `ANALYZE` (or `PRAGMA optimize`) before evaluating plans on tables with real data. Without statistics, the planner uses heuristics that may not reflect actual row counts.

## Anti-Patterns That Cause Full Table Scans

### Correlated subqueries instead of JOINs

```sql
-- BAD: subquery runs once per order row
SELECT o.id,
  (SELECT name FROM customers WHERE id = o.customer_id) AS customer_name
FROM orders o;

-- GOOD: single join
SELECT o.id, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id;
```

MUST rewrite correlated scalar subqueries in SELECT lists as JOINs when the subquery is the bottleneck. The planner labels these `CORRELATED SCALAR SUBQUERY` in EXPLAIN output.

### Functions on indexed columns in WHERE

Wrapping an indexed column in a function prevents index use.

```sql
-- BAD: index on created_date is not used
WHERE date(created_date) = '2024-01-15'

-- GOOD: index is used
WHERE created_date >= '2024-01-15' AND created_date < '2024-01-16'

-- ALTERNATIVE: create an expression index to match the function call
CREATE INDEX idx_date ON orders(date(created_date));
```

MUST NOT apply functions to indexed filter columns unless a matching expression index exists.

### UNION when UNION ALL suffices

```sql
-- BAD: sorts all rows to deduplicate (often unnecessary)
SELECT id FROM active_users
UNION
SELECT id FROM archived_users;

-- GOOD: appends results directly
SELECT id FROM active_users
UNION ALL
SELECT id FROM archived_users;
```

Use `UNION ALL` when the result sets are known to be disjoint, or when duplicates are acceptable. `UNION` can be 60%+ slower on large datasets due to the sort and deduplication pass.

### SELECT * when specific columns suffice

```sql
-- BAD: fetches all columns, prevents covering index optimization
SELECT * FROM orders WHERE status = 'active';

-- GOOD: may use a covering index
SELECT id, customer_id FROM orders WHERE status = 'active';
```

SHOULD select only the columns the caller needs. This enables covering index optimization and reduces data transfer.

### NOT IN with subqueries (NULL hazard)

```sql
-- DANGEROUS: if the subquery returns any NULL, NOT IN evaluates to NULL,
-- returning zero rows regardless of other values
SELECT * FROM orders WHERE customer_id NOT IN (SELECT id FROM inactive_customers);

-- SAFE: NOT EXISTS handles NULLs correctly
SELECT * FROM orders o
WHERE NOT EXISTS (
  SELECT 1 FROM inactive_customers ic WHERE ic.id = o.customer_id
);
```

MUST use `NOT EXISTS` instead of `NOT IN` with subqueries. The NULL behavior of `NOT IN` causes silent data loss.

### OR conditions without indexes on both sides

```sql
-- Potentially slow without indexes on both columns
WHERE status = 'active' OR priority > 5
```

SQLite uses `MULTI-INDEX OR` if both columns are indexed independently. Without indexes on both columns, it falls back to a full scan. Either index both columns or restructure as a `UNION ALL`.

## Query Planner Optimizations to Leverage

**Skip-scan:** When the leftmost index column has few distinct values, the planner can skip-scan the index using a later constrained column. Requires `ANALYZE` to have been run (planner needs statistics showing 18+ duplicate values in the leftmost column).

**MIN/MAX optimization:** `SELECT MIN(col)` or `SELECT MAX(col)` on the leftmost column of an index executes as a single index lookup, not a full scan.

**LIKE range optimization:** `WHERE col LIKE 'prefix%'` on a column with BINARY collation is rewritten as a range scan: `col >= 'prefix' AND col < 'prefiy'`. Wildcards at the start (`LIKE '%suffix'`) prevent this optimization.

**Constant propagation:** `WHERE a = b AND b = 5` implies `a = 5`, letting the planner use an index on `a`.

**OR-to-IN conversion:** `WHERE x = 1 OR x = 2 OR x = 3` is rewritten as `WHERE x IN (1, 2, 3)` for index use.

**Subquery flattening:** SQLite merges FROM-clause subqueries into the outer query where possible, enabling index use on the underlying tables. This does not always apply — check `MATERIALIZE` in EXPLAIN output to see when it does not.

## CTEs vs Subqueries

CTEs (`WITH` clauses) improve readability but have a performance tradeoff in SQLite.

- SQLite materializes CTEs referenced more than once (stores the result in a temp table). This prevents the planner from pushing WHERE predicates into the CTE.
- A subquery in a FROM clause may be flattened into the outer query, preserving index use on the underlying table.

```sql
-- CTE: readable but materialized; WHERE on the outer query does not push into it
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_date > '2026-01-01'
)
SELECT * FROM recent_orders WHERE customer_id = 42;

-- Subquery: may be flattened; planner can use index on both conditions
SELECT * FROM (
  SELECT * FROM orders WHERE created_date > '2026-01-01'
) WHERE customer_id = 42;
```

SHOULD use CTEs for clarity. SHOULD switch to subqueries if `EXPLAIN QUERY PLAN` shows the CTE is being materialized and causing a performance problem.

## Running ANALYZE

The query planner makes better decisions with current statistics. Without them, it uses heuristics that can pick the wrong index or miss skip-scan opportunities.

```sql
-- Collect statistics for all tables
ANALYZE;

-- Collect for one table (faster)
ANALYZE orders;

-- Limit analysis time (rows examined per index)
PRAGMA analysis_limit = 1000;
ANALYZE;

-- Inspect collected statistics
SELECT * FROM sqlite_stat1;
```

SHOULD run `PRAGMA optimize` on connection open for long-lived connections. SHOULD run `ANALYZE` after bulk inserts or major schema changes. Statistics are stored in `sqlite_stat1` and used on subsequent connections.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
