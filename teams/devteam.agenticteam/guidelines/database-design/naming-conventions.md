---

id: DDE1B6FD-773C-4F9F-A328-51150468BC99
title: "Database naming conventions"
domain: agentic-cookbook://guidelines/implementing/data/naming-conventions
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Snake_case naming rules for tables, columns, primary keys, foreign keys, indexes, constraints, and triggers — including reserved word avoidance."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - naming
  - schema-design
  - conventions
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://www.sqlite.org/lang_keywords.html
  - https://dev.to/ovid/database-naming-standards-2061
  - https://www.bbkane.com/blog/sql-naming-conventions/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Database naming conventions

Consistent naming makes schemas self-documenting and prevents subtle bugs. These rules apply to all identifiers: tables, columns, indexes, constraints, and triggers.

## Use snake_case everywhere

ALL identifiers MUST use `snake_case`. SQL is case-insensitive for identifiers, so `CamelCase` creates false visual distinctions (`UnderValue` and `Undervalue` are identical to the engine). Underscores are unambiguous, readable across tools, and work well for non-native English speakers.

```sql
-- Correct
CREATE TABLE workflow_run (
    workflow_run_id  INTEGER PRIMARY KEY,
    workflow_name    TEXT NOT NULL,
    creation_date    TEXT NOT NULL DEFAULT (datetime('now')),
    is_active        INTEGER NOT NULL DEFAULT 1
);

-- Wrong
CREATE TABLE WorkflowRun (WorkflowRunID INTEGER PRIMARY KEY, ...);
```

## Table names

Pick singular or plural and be consistent within a project. **Prefer singular** when compound names are common (`workflow_run` composes more naturally than `workflows_runs`). **Prefer plural** when avoiding SQL reserved word collisions matters (`users` avoids the reserved word `user`).

Whatever you choose, document it and never mix within a single schema.

## Primary key columns

MUST use `<table_name>_id`, not bare `id`. Self-documenting PKs make JOIN bugs immediately visible:

```sql
-- Correct: mismatch is obvious
SELECT * FROM audit_log al
JOIN actors a ON a.actor_id = al.changed_by_actor_id;

-- Wrong: mismatches are invisible
SELECT * FROM audit_log al
JOIN actors a ON a.id = al.changed_by;
```

## Foreign key columns

MUST match the referenced column name when possible. When a table references the same parent table more than once, add a descriptive qualifier:

```sql
-- Single reference: match parent PK name
finding_id INTEGER REFERENCES findings(finding_id)

-- Multiple references to same parent: add qualifier
source_actor_id      INTEGER REFERENCES actors(actor_id),
destination_actor_id INTEGER REFERENCES actors(actor_id)
```

## Boolean columns

MUST be prefixed with `is_` or `has_`:

```sql
is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
has_children INTEGER NOT NULL DEFAULT 0 CHECK (has_children IN (0, 1))
```

## Date/time columns

MUST use descriptive event names. Avoid vague suffixes like `_at`:

```sql
-- Correct
creation_date     TEXT NOT NULL DEFAULT (datetime('now')),
modification_date TEXT,
completion_date   TEXT

-- Wrong
created_at TEXT,
updated_at TEXT
```

## Reserved words to avoid

SQLite has 147 reserved keywords. These are common traps:

| Avoid | Use instead |
|-------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| `order` | `sort_order`, `display_order` |
| `group` | `team`, `grouping` |
| `index` | `position`, `sort_index` |
| `key` | `lookup_key`, `api_key` |
| `value` | `setting_value`, `metric_value` |
| `action` | `operation`, `activity` |
| `check` | `validation`, `check_result` |
| `default` | `default_value`, `fallback` |
| `filter` | `criterion`, `filter_expr` |
| `plan` | `execution_plan` |
| `row` | `record`, `entry` |
| `query` | `search_query` |

If you must use a reserved word, quote it with double quotes (`"order"`), but this adds friction to every query. Renaming is always preferred.

SQLite adds new keywords over time. The official docs recommend quoting any English word used as an identifier, even if not currently reserved.

## Indexes, constraints, and triggers

Use these prefixes for all named objects:

```sql
-- Indexes: ix_tablename_purpose
CREATE INDEX ix_findings_workflow_run_id ON findings(workflow_run_id);
CREATE UNIQUE INDEX ux_actors_email ON actors(email);

-- Check constraints: ck_tablename_column
CONSTRAINT ck_employees_salary CHECK (salary > 0)

-- Triggers: tr_tablename_event_purpose
CREATE TRIGGER tr_documents_after_update_audit ...
```

The prefix makes object type immediately clear in schema dumps and `sqlite_schema` queries.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
