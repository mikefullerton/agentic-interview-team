"""SQLite backend for the arbitrator.

Uses the stdlib `sqlite3` module with `asyncio.to_thread` to keep the async
contract. Good enough for the walking skeleton and avoids an `aiosqlite`
dependency.
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

from .base import Storage


SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class SqliteBackend(Storage):
    def __init__(self, db_path: str | Path):
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        def _open() -> sqlite3.Connection:
            conn = sqlite3.connect(self._db_path, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(SCHEMA_PATH.read_text())
            return conn

        self._conn = await asyncio.to_thread(_open)

    async def close(self) -> None:
        if self._conn is not None:
            conn = self._conn
            self._conn = None
            await asyncio.to_thread(conn.close)

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SqliteBackend not connected")
        return self._conn

    async def insert(self, table: str, row: dict[str, Any]) -> None:
        async with self._lock:
            conn = self._require_conn()
            cols = ", ".join(row.keys())
            placeholders = ", ".join("?" for _ in row)
            sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            values = tuple(row.values())
            await asyncio.to_thread(conn.execute, sql, values)

    async def update(
        self, table: str, key: dict[str, Any], updates: dict[str, Any]
    ) -> None:
        async with self._lock:
            conn = self._require_conn()
            set_clause = ", ".join(f"{c} = ?" for c in updates)
            where_clause = " AND ".join(f"{c} = ?" for c in key)
            sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            values = tuple(updates.values()) + tuple(key.values())
            await asyncio.to_thread(conn.execute, sql, values)

    async def fetch_one(
        self, table: str, key: dict[str, Any]
    ) -> dict[str, Any] | None:
        async with self._lock:
            conn = self._require_conn()
            where_clause = " AND ".join(f"{c} = ?" for c in key)
            sql = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"
            values = tuple(key.values())
            cursor = await asyncio.to_thread(conn.execute, sql, values)
            row = await asyncio.to_thread(cursor.fetchone)
            return dict(row) if row else None

    async def fetch_all(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        async with self._lock:
            conn = self._require_conn()
            sql = f"SELECT * FROM {table}"
            values: tuple[Any, ...] = ()
            if where:
                where_clause = " AND ".join(f"{c} = ?" for c in where)
                sql += f" WHERE {where_clause}"
                values = tuple(where.values())
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit is not None:
                sql += f" LIMIT {int(limit)}"
            cursor = await asyncio.to_thread(conn.execute, sql, values)
            rows = await asyncio.to_thread(cursor.fetchall)
            return [dict(r) for r in rows]
