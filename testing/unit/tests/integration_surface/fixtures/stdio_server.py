"""Subprocess entry point: `python -m stdio_server` style harness.

Reads a JSON-serialized FakeTeam script from `AGENTIC_FAKE_SCRIPT`, wires
an `InProcessSession(FakeTeam)` behind a `serve_stdio` loop, and runs
until stdin closes. Used by the stdio transport test suite so contract
tests can exercise the stdio path with a controlled fake runtime.

Script shape:

    {
      "replies": [
        {
          "events": [["text", {"text": "hi"}], ["result", {"stop_reason": "end_turn"}]],
          "ask": null,
          "after_answer": []
        }
      ]
    }
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))
sys.path.insert(0, str(REPO_ROOT / "testing" / "unit" / "tests"))

from services.integration_surface import (  # noqa: E402
    InProcessSession,
    serve_stdio,
)

from integration_surface.fixtures.fake_team import FakeTeam  # noqa: E402


def _build_fake_from_script(script: dict) -> FakeTeam:
    fake = FakeTeam()
    for reply in script.get("replies", []):
        events = [(t, p) for t, p in reply.get("events", [])]
        ask = reply.get("ask")
        if ask is not None:
            post = [(t, p) for t, p in reply.get("after_answer", [])]
            fake.reply_with_question(events, tuple(ask), post)
        else:
            fake.reply(*events)
    return fake


async def _main() -> None:
    script = json.loads(os.environ.get("AGENTIC_FAKE_SCRIPT") or "{}")
    fake = _build_fake_from_script(script)
    session = InProcessSession(fake)

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    await serve_stdio(session, reader, sys.stdout.buffer)


if __name__ == "__main__":
    asyncio.run(_main())
