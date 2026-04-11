"""Storage protocol — narrow surface that concrete backends implement."""
from __future__ import annotations

from typing import Any, Protocol


class Storage(Protocol):
    """Minimal row-level operations. The arbitrator composes higher-level ops."""

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def insert(self, table: str, row: dict[str, Any]) -> None: ...
    async def update(
        self, table: str, key: dict[str, Any], updates: dict[str, Any]
    ) -> None: ...
    async def fetch_one(
        self, table: str, key: dict[str, Any]
    ) -> dict[str, Any] | None: ...
    async def fetch_all(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]: ...
