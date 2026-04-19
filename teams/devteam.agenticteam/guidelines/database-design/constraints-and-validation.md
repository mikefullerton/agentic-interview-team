---

id: F28A4638-C2AE-4A9B-817F-0F19B5712168
title: "Constraints and validation"
domain: agentic-cookbook://guidelines/implementing/data/constraints-and-validation
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "CHECK constraints for SQLite: evaluation rules, enum-like constraints, boolean enforcement, range and pattern validation, NULL truthiness, and limitations."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - constraints
  - validation
  - schema-design
  - check-constraints
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://www.sqlite.org/lang_createtable.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Constraints and validation

CHECK constraints are the primary mechanism for enforcing data validity at the schema level in SQLite. Used correctly, they catch bad data at insert/update time rather than during application reads.

## Syntax

```sql
-- Column-level
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    quantity   INTEGER NOT NULL CHECK (quantity >= 0),
    price      REAL NOT NULL CHECK (price > 0)
);

-- Table-level (can reference multiple columns)
CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    CHECK (end_date >= start_date)
);

-- Named constraint (recommended for large schemas)
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    salary      REAL NOT NULL,
    CONSTRAINT ck_employees_salary CHECK (salary > 0)
);
```

There is no functional difference between column-level and table-level CHECK constraints. Use table-level only when the expression references multiple columns.

## How CHECK evaluation works

1. The expression is evaluated on every INSERT and UPDATE
2. The result is cast to NUMERIC
3. Integer `0` or real `0.0` → constraint violation (`SQLITE_CONSTRAINT_CHECK`)
4. `NULL` → **no violation** (NULL is not zero)
5. Any other non-zero value → no violation

**The NULL gotcha.** `CHECK (status IN ('active', 'inactive'))` permits NULL values because `NULL IN (...)` evaluates to NULL, which is not zero. If NULL should be prohibited, add `NOT NULL` as a separate constraint — it is not implied by CHECK.

## Common validation patterns

**Enum-like (restricted values):**

```sql
status    TEXT NOT NULL CHECK (status IN ('pending', 'active', 'completed', 'failed')),
priority  INTEGER NOT NULL CHECK (priority IN (1, 2, 3, 4, 5)),
direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound'))
```

**Boolean enforcement:**

```sql
is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
```

**Range validation:**

```sql
age     INTEGER NOT NULL CHECK (age >= 0 AND age <= 150),
score   REAL NOT NULL CHECK (score BETWEEN 0.0 AND 100.0),
percent INTEGER NOT NULL CHECK (percent >= 0 AND percent <= 100)
```

**Pattern matching:**

```sql
email TEXT NOT NULL CHECK (email LIKE '%_@_%.__%'),
phone TEXT CHECK (phone LIKE '+%' OR phone IS NULL),
code  TEXT NOT NULL CHECK (
    length(code) = 6 AND code GLOB '[A-Z][A-Z][0-9][0-9][0-9][0-9]'
)
```

**String length:**

```sql
username TEXT NOT NULL CHECK (length(username) >= 3 AND length(username) <= 50),
api_key  TEXT NOT NULL CHECK (length(api_key) = 32)
```

**Multi-column constraint:**

```sql
CHECK (end_date > start_date),
CHECK (discount > 0 AND discount <= 1.0)
```

**Conditional logic:**

```sql
CHECK (
    (status = 'surplus' AND stock >= 500) OR
    (status != 'surplus')
)
```

## What is NOT allowed in CHECK expressions

These are explicitly prohibited:

| Prohibited | Alternative |
|------------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Subqueries (`SELECT ...`) | Use triggers for cross-row validation |
| `CURRENT_TIME` | Application-level validation |
| `CURRENT_DATE` | Application-level validation |
| `CURRENT_TIMESTAMP` | Application-level validation |

Date validation that depends on "now" (e.g., `CHECK (event_date <= CURRENT_DATE)`) cannot be expressed in a schema constraint. Use triggers or application-layer validation instead.

## Limitations

**Cannot be added via ALTER TABLE.** Adding a CHECK constraint to an existing table requires the full recreate-copy-drop-rename procedure. Design constraints upfront.

**Row-scoped only.** CHECK constraints cannot reference other rows or tables. For cross-row validation, use triggers.

**Not verified on SELECT.** Data that bypassed constraints (via external file manipulation or `PRAGMA ignore_check_constraints`) can be read even if it violates constraints.

**Conflict resolution is always ABORT.** The `ON CONFLICT` clause is parsed but ignored for CHECK constraints — violations always abort the statement.

## Disabling for data import

When importing potentially dirty data:

```sql
PRAGMA ignore_check_constraints = ON;
-- Import data...
PRAGMA ignore_check_constraints = OFF;
```

After import, verify integrity:

```sql
PRAGMA integrity_check;
```

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
