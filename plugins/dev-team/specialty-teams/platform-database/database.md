---
name: database
description: SQLite with WAL mode for concurrent read access; no ORM — direct SQL via `sqlite3` standard library; `PRAGMA journal_mod...
artifact: guidelines/language/python/database.md
version: 1.0.0
---

## Worker Focus
SQLite with WAL mode for concurrent read access; no ORM — direct SQL via `sqlite3` standard library; `PRAGMA journal_mode=WAL` set on connection open

## Verify
`PRAGMA journal_mode=WAL` present in connection setup; no ORM imports (SQLAlchemy, Django ORM, etc.); raw `sqlite3` module used for all queries
