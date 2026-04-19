---

id: CBFA06B6-EC22-4784-9E61-C99307064B72
title: "JSON columns and generated columns"
domain: agentic-cookbook://guidelines/implementing/data/json-columns
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "JSON storage and extraction in SQLite, json_each for array iteration, generated columns for indexing JSON fields, and when JSON is a schema design smell."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - json
  - generated-columns
  - schema-design
  - indexing
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://sqlite.org/json1.html
  - https://sqlite.org/gencol.html
  - https://www.dbpro.app/blog/sqlite-json-virtual-columns-indexing
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# JSON columns and generated columns

SQLite stores JSON as `TEXT`. The built-in `json1` functions let you query into JSON values without fully deserializing them. When combined with generated columns and indexes, JSON fields can be queried with B-tree speed.

## JSON storage

Declare a JSON column as `TEXT`. Validate at insert time if needed:

```sql
CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY,
    body        TEXT NOT NULL CHECK (json_valid(body))
);
```

`json_valid()` returns 1 for valid JSON, 0 for invalid. Use this CHECK constraint when data integrity matters.

## Extraction operators

Two operators for extracting values:

```sql
-- ->> always returns a SQL type (TEXT, INTEGER, REAL, or NULL)
SELECT body ->> '$.author' FROM documents;

-- -> always returns a JSON text representation
SELECT body -> '$.tags' FROM documents;
-- For {"tags": [1,2]} returns: '[1,2]'

-- json_extract: equivalent to ->> for scalars, returns JSON text for objects/arrays
SELECT json_extract(body, '$.author') FROM documents;
```

MUST use `->>`  when you want the value for comparison or filtering. Use `->` when you need the JSON text of a nested object or array.

`->>` requires SQLite 3.38.0+. For older SQLite, use `json_extract()`.

## Iterating arrays with json_each

```sql
-- Find documents tagged with 'urgent'
SELECT DISTINCT d.document_id
FROM documents d, json_each(d.body, '$.tags') t
WHERE t.value = 'urgent';

-- Find users with a 704 area code phone number
SELECT DISTINCT user.name
FROM user, json_each(user.phone)
WHERE json_each.value LIKE '704-%';
```

`json_each` is a table-valued function that returns one row per array element or object property.

## Modifying JSON

```sql
-- json_set: creates or overwrites a key
UPDATE documents SET body = json_set(body, '$.status', 'processed');

-- json_insert: creates only (will not overwrite existing key)
UPDATE documents SET body = json_insert(body, '$.new_field', 42);

-- json_replace: overwrites only (will not create missing key)
UPDATE documents SET body = json_replace(body, '$.status', 'done');

-- Append to an array ($[#] is the end position)
UPDATE documents SET body = json_set(body, '$.tags[#]', 'new-tag');

-- Remove a key
UPDATE documents SET body = json_remove(body, '$.temp_field');
```

## Aggregating rows into JSON

```sql
-- Build a JSON array from rows
SELECT json_group_array(json_object('id', document_id, 'title', title))
FROM documents;
-- Returns: [{"id":1,"title":"..."}, ...]

-- Build a JSON object from rows
SELECT json_group_object(name, score) FROM leaderboard;
-- Returns: {"alice":100, "bob":85}
```

## Generated columns for indexing JSON fields

This is the key pattern for JSON performance. Virtual generated columns expose JSON fields as real columns that can be indexed:

```sql
CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY,
    body        TEXT NOT NULL
);

-- Add virtual generated columns (no disk space used; computed on read)
ALTER TABLE documents ADD COLUMN doc_type TEXT
    GENERATED ALWAYS AS (body ->> '$.type') VIRTUAL;

ALTER TABLE documents ADD COLUMN author TEXT
    GENERATED ALWAYS AS (body ->> '$.author') VIRTUAL;

-- Index the generated columns for B-tree performance
CREATE INDEX ix_documents_doc_type ON documents(doc_type);
CREATE INDEX ix_documents_author ON documents(author);

-- Queries now use the indexes
SELECT * FROM documents WHERE doc_type = 'report' AND author = 'alice';
```

**VIRTUAL vs STORED:**
- `VIRTUAL`: computed on read, no disk space, can be added with `ALTER TABLE`
- `STORED`: computed on write, uses disk space, cannot be added with `ALTER TABLE`

SHOULD prefer `VIRTUAL` unless reads vastly outnumber writes and the extraction expression is expensive.

You can also index JSON fields directly without generated columns:

```sql
CREATE INDEX ix_documents_color ON documents(body ->> '$.color');
```

This works but makes the index expression visible in queries. Named generated columns are clearer and reusable.

## When JSON is a schema design smell

JSON is appropriate for:
- Variable or unpredictable attribute sets (product catalogs with per-category attributes)
- Configuration or settings blobs where the structure evolves
- Sync payloads and API responses stored verbatim

JSON is NOT appropriate for:
- Any field you would `WHERE`, `JOIN`, or `ORDER BY` regularly — make it a typed column
- One-to-many relationships — use a separate table
- Data that needs referential integrity or type enforcement

**The rule:** if a JSON field is queried in more than occasional ad-hoc queries, promote it to a real column. Add a generated column + index as the intermediate step before full promotion.

## PostgreSQL compatibility notes

- SQLite's `->` and `->>` operators are designed to be syntactically compatible with PostgreSQL
- SQLite JSONB is NOT binary-compatible with PostgreSQL JSONB — they are different on-disk formats
- SQLite's `json1` returns NULL for invalid JSON; PostgreSQL raises an error — validate on both sides
- PostgreSQL JSONB supports GIN indexes; SQLite uses B-tree indexes on generated columns or expressions

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
