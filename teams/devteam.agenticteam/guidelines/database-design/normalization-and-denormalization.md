---

id: C8B92187-7C2F-4D11-9AB3-EC806F3CDF26
title: "Normalization and denormalization"
domain: agentic-cookbook://guidelines/implementing/data/normalization-and-denormalization
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Start normalized (3NF), denormalize only measured hotspots. SQLite-specific tradeoffs and sync-safe denormalization guidance."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - normalization
  - denormalization
  - schema-design
  - performance
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://sqleditor.online/blog/sqlite-schema-design-patterns
  - https://blog.bytebytego.com/p/database-schema-design-simplified
  - https://maximeblanc.fr/blog/sqlite-json-and-denormalization
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Normalization and denormalization

## Default: start normalized (3NF)

New schemas SHOULD start at third normal form (3NF). A normalized schema:

- Eliminates redundancy — each fact is stored once
- Prevents update anomalies — changing one thing means changing it in one place
- Keeps storage compact

3NF requires:
1. Each column depends on the whole primary key (1NF, 2NF)
2. Each non-key column depends only on the primary key, not on other non-key columns

```sql
-- Normalized: artist is stored once, not duplicated per track
CREATE TABLE artists (
    artist_id   INTEGER PRIMARY KEY,
    artist_name TEXT NOT NULL
);

CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER NOT NULL REFERENCES artists(artist_id)
);
```

## When to denormalize

Denormalization deliberately introduces redundancy to speed up specific read patterns. ONLY denormalize when:

1. A join has been **measured** as a performance bottleneck
2. The data is **read far more than written**
3. You have a strategy for **keeping the redundant copy in sync**

Do not denormalize preemptively based on assumptions. Measure first.

**Example: denormalize a frequently-displayed display name**

```sql
-- Instead of joining to actors on every audit log query,
-- copy display_name onto the supertype table for fast reads
CREATE TABLE actors (
    actor_id     INTEGER PRIMARY KEY,
    actor_type   TEXT NOT NULL,
    display_name TEXT NOT NULL  -- denormalized from subtypes
);
```

## SQLite-specific considerations

SQLite is embedded — there is zero network latency for queries. The N+1 query problem that drives aggressive denormalization in client/server databases (PostgreSQL, MySQL) is far less severe in SQLite. Multiple simple queries often outperform a single complex JOIN.

**Implication:** The threshold for denormalization in SQLite is higher than in networked databases. Prefer normalized schemas unless benchmarks prove otherwise.

Benchmark reference: in one test across 5,000 records, a denormalized schema was 16x faster for one query pattern and 104x faster for another — but was also 50% smaller. In SQLite, denormalization can simultaneously improve speed and reduce size because it eliminates B-tree traversals on join columns.

## Sync-safe denormalization

When syncing SQLite with a server database, denormalized columns add sync complexity. Each write to the source data must also propagate to denormalized copies.

Rules for denormalization in sync-capable schemas:
- MUST maintain the denormalized column via trigger so it stays in sync within the local database
- MUST include the denormalized column in sync payloads so the server stays consistent
- SHOULD treat the authoritative value as the normalized source; the denormalized copy is derived
- Prefer denormalizing immutable or rarely-changing data (names, labels) over frequently-changing values

```sql
-- Trigger to maintain denormalized display_name on actors when humans table changes
CREATE TRIGGER tr_humans_after_update_display_name
AFTER UPDATE OF name ON humans
BEGIN
    UPDATE actors
    SET display_name = NEW.name
    WHERE actor_id = NEW.actor_id;
END;
```

## Anti-patterns to avoid

**Storing computed values.** Do not store counts, totals, or derived booleans as columns. Query the rows to compute them. Computed columns become stale and require maintenance triggers.

**Storing summaries or narratives.** Unstructured text that you would not `WHERE`, `JOIN`, or `ORDER BY` does not belong in a column. Use JSON if the structure is needed but not indexed.

**Storing one-to-many relationships as lists in a column.** A comma-separated list of IDs in a single column is a normalization violation. Make it a separate table with one row per item.

## Decision guide

| Situation | Recommendation |
|-----------|---------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| New schema, unknown access patterns | Start at 3NF |
| Read-heavy dashboard, measured join bottleneck | Denormalize the join |
| Audit log display_name | Denormalize onto supertype table |
| Synced table with denormalized column | Maintain via trigger; include in sync payload |
| Count or sum of child rows | Do not store; query the child table |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
