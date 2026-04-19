---

id: 246D87C8-213A-4DE1-9452-6E683D3D75E3
title: "Relationship patterns"
domain: agentic-cookbook://guidelines/implementing/data/relationships
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "One-to-many, many-to-many, polymorphic FKs, self-referential tables, and tree hierarchy patterns with tradeoffs and SQLite-specific guidance."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - relationships
  - schema-design
  - polymorphic
  - hierarchies
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/foreign-keys.md
references:
  - https://teddysmith.io/sql-trees/
  - https://www.bytebase.com/blog/database-design-patterns/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Relationship patterns

## One-to-many

The standard relationship pattern. A child table holds a FK column referencing the parent's PK:

```sql
CREATE TABLE artists (
    artist_id   INTEGER PRIMARY KEY,
    artist_name TEXT NOT NULL
);

CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER NOT NULL REFERENCES artists(artist_id)
);

-- Always index the FK column
CREATE INDEX ix_tracks_artist_id ON tracks(artist_id);
```

## Many-to-many

Use a junction table with FKs to both parent tables. The junction table's PK SHOULD be a composite of both FKs:

```sql
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL
);

CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    title     TEXT NOT NULL
);

CREATE TABLE enrollments (
    student_id  INTEGER NOT NULL REFERENCES students(student_id),
    course_id   INTEGER NOT NULL REFERENCES courses(course_id),
    enrolled_on TEXT NOT NULL DEFAULT (date('now')),
    PRIMARY KEY (student_id, course_id)
);
```

Add additional indexes if you query the junction from either direction:

```sql
CREATE INDEX ix_enrollments_course_id ON enrollments(course_id);
```

## Polymorphic foreign keys

A polymorphic FK references one of several different tables. A common example: an audit log where the actor could be a human, a service, or a bot.

### Pattern 1: Generic FK with discriminator column

```sql
CREATE TABLE audit_log (
    audit_log_id    INTEGER PRIMARY KEY,
    changed_by_id   INTEGER NOT NULL,
    changed_by_type TEXT NOT NULL CHECK (changed_by_type IN ('human', 'service', 'bot'))
);
```

Simple, works everywhere. SQLite cannot enforce FK integrity across multiple tables even with `PRAGMA foreign_keys = ON` — the application owns that constraint. Easy to get into an inconsistent state without discipline.

### Pattern 2: Supertype / base table (recommended)

```sql
CREATE TABLE actors (
    actor_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_type   TEXT NOT NULL CHECK (actor_type IN ('human', 'service', 'bot')),
    display_name TEXT NOT NULL  -- denormalized for fast queries
);

CREATE TABLE humans (
    actor_id INTEGER PRIMARY KEY REFERENCES actors(actor_id),
    email    TEXT NOT NULL UNIQUE
);

CREATE TABLE services (
    actor_id     INTEGER PRIMARY KEY REFERENCES actors(actor_id),
    service_name TEXT NOT NULL
);

CREATE TABLE audit_log (
    audit_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_by   INTEGER NOT NULL REFERENCES actors(actor_id),
    change_date  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`audit_log.changed_by` is a real, enforced FK into the supertype table. Each subtype has a 1:1 FK back to the supertype. Denormalize `display_name` onto the supertype to avoid subtype joins for common display queries.

**Use Pattern 2** when actor types share a common identity concept and referential integrity matters. **Use Pattern 1** when moving fast and comfortable enforcing integrity in application code.

### Pattern 3: Nullable column per type

```sql
CREATE TABLE audit_log (
    audit_log_id           INTEGER PRIMARY KEY,
    changed_by_human_id    INTEGER REFERENCES humans(actor_id),
    changed_by_service_id  INTEGER REFERENCES services(actor_id),
    CHECK (
        (changed_by_human_id   IS NOT NULL) +
        (changed_by_service_id IS NOT NULL) = 1
    )
);
```

Gives real FK enforcement on each column. Gets unwieldy when types grow beyond 3–4.

## Self-referential (adjacency list)

For hierarchical data, the simplest approach is a `parent_id` FK referencing the same table:

```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    parent_id   INTEGER REFERENCES categories(category_id)  -- NULL = root
);
CREATE INDEX ix_categories_parent_id ON categories(parent_id);
```

Finding immediate children: `WHERE parent_id = ?`. Finding all descendants requires a recursive CTE (SQLite 3.8.3+):

```sql
WITH RECURSIVE descendants AS (
    SELECT category_id, name, parent_id FROM categories WHERE category_id = ?
    UNION ALL
    SELECT c.category_id, c.name, c.parent_id
    FROM categories c
    JOIN descendants d ON c.parent_id = d.category_id
)
SELECT * FROM descendants;
```

## Tree hierarchies

| Pattern | Read performance | Write complexity | Storage | Best for |
|---------|-----------------|-----------------|---------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Adjacency list | Moderate (recursive) | Simple | Minimal | Dynamic trees with occasional depth queries |
| Closure table | Excellent | Moderate | High | Read-heavy, deep hierarchies |
| Nested sets | Excellent | High (renumbering) | Low | Static / rarely-modified hierarchies |

**Closure table** stores every ancestor-descendant path as a row, enabling efficient non-recursive queries:

```sql
CREATE TABLE category_closure (
    ancestor_id   INTEGER NOT NULL REFERENCES categories(category_id),
    descendant_id INTEGER NOT NULL REFERENCES categories(category_id),
    depth         INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ancestor_id, descendant_id)
);

-- All descendants of node 1:
SELECT descendant_id FROM category_closure WHERE ancestor_id = 1;

-- Direct children only:
SELECT descendant_id FROM category_closure WHERE ancestor_id = 1 AND depth = 1;
```

Tradeoff: O(n²) worst-case storage and complex insert/delete maintenance.

**Nested sets** encode hierarchy as left/right boundary integers. Excellent read performance but inserting or moving a node requires renumbering all boundaries — impractical for frequently-modified trees.

**Start with adjacency list.** Migrate to closure table only if recursive queries become a measured performance problem.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
