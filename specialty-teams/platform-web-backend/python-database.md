---
name: python-database
description: SQLite with WAL mode (`PRAGMA journal_mode=WAL`), `sqlite3` standard library (no ORM), direct SQL queries
artifact: guidelines/language/python/database.md
version: 1.0.0
---

## Worker Focus
SQLite with WAL mode (`PRAGMA journal_mode=WAL`), `sqlite3` standard library (no ORM), direct SQL queries

## Verify
WAL mode pragma set on connection; no SQLAlchemy or ORM import; `sqlite3` module used directly; parameterized queries only (no string concatenation)
