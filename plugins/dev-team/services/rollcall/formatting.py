"""Roll-call output renderers — table for humans, NDJSON for machines."""
from __future__ import annotations

import json
from typing import Iterable

from .orchestrator import RollCallResult


def _status(r: RollCallResult) -> str:
    if r.error is None:
        return "ok"
    return "failed"


def render_table(results: Iterable[RollCallResult]) -> str:
    results = list(results)
    header = ("TEAM", "ROLE", "STATUS", "TIME", "NOTE")
    rows: list[tuple[str, str, str, str, str]] = [header]
    for r in results:
        role_label = f"{r.role.kind}/{r.role.name}"
        time_label = f"{r.duration_ms / 1000:.1f}s"
        note = r.error.message if r.error is not None else ""
        rows.append((r.role.team, role_label, _status(r), time_label, note))

    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    lines = []
    for row in rows:
        line = "  ".join(
            cell.ljust(widths[i]) for i, cell in enumerate(row)
        )
        lines.append(line.rstrip())
    return "\n".join(lines) + "\n"


def render_json(results: Iterable[RollCallResult]) -> str:
    """NDJSON — one result per line."""
    out_lines = []
    for r in results:
        out_lines.append(json.dumps({
            "team": r.role.team,
            "kind": r.role.kind,
            "name": r.role.name,
            "status": _status(r),
            "duration_ms": r.duration_ms,
            "response": r.response,
            "error": (
                None if r.error is None
                else {"kind": r.error.kind, "message": r.error.message}
            ),
        }, separators=(",", ":"), sort_keys=True))
    return "\n".join(out_lines) + ("\n" if out_lines else "")
