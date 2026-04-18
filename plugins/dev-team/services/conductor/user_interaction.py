"""User-interaction primitives for realizers.

Phase 1 of "real interview" support: `ask_user` opens a question gate
on the session, emits the question as a user-facing message, and
blocks until the gate is resolved. The returned string is the verdict
the user (or a supervising process) chose.

UI channels (TUI, web, REPL, or tests) observe the gate/message and
respond by calling `arbitrator.resolve_gate(gate_id, verdict=answer)`.
The conductor itself doesn't need to know which UI is connected.
"""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID


async def ask_user(
    arbitrator,  # Arbitrator
    session_id: UUID,
    question: str,
    options: list[str],
    *,
    plan_node_id: str | None = None,
    team_id: str = "conductor",
    poll_interval: float = 0.05,
) -> str:
    """Ask the user a question and wait for an answer.

    Opens a gate with category="question", emits the question as a
    message for UIs to render, then polls the gate row until its
    verdict is non-null. Returns the verdict string.

    `options` is the allowed answer set. For open-ended questions,
    pass a single-element list like `["*"]` and interpret accordingly.
    """
    gate = await arbitrator.create_gate(
        session_id=session_id,
        team_id=team_id,
        category="question",
        options=options,
        plan_node_id=plan_node_id,
    )
    await arbitrator.create_message(
        session_id=session_id,
        team_id=team_id,
        direction="out",
        type="question",
        body=question,
        plan_node_id=plan_node_id,
    )
    storage = arbitrator._storage
    while True:
        row = await storage.fetch_one("gate", {"gate_id": gate.gate_id})
        if row and row.get("verdict"):
            return str(row["verdict"])
        await asyncio.sleep(poll_interval)


async def answer_pending_gates(
    arbitrator,
    session_id: UUID,
    answers: dict[str, str],
) -> None:
    """Test helper: scan for open question gates and answer them.

    `answers` is keyed by a substring of the question body. The helper
    finds each pending (verdict-null) question gate, reads the most
    recent question message for its plan_node_id, and resolves the gate
    with the mapped verdict on the first matching key.
    """
    storage = arbitrator._storage
    gate_rows = await storage.fetch_all(
        "gate", where={"session_id": str(session_id)}
    )
    # Bodies live in the `body` side-table, not on the message row.
    messages = await arbitrator.list_messages(session_id)
    latest_question_body_by_node: dict[str | None, str] = {}
    for m in messages:
        if m.type == "question":
            latest_question_body_by_node[m.plan_node_id] = m.body

    for g in gate_rows:
        if g.get("verdict") is not None:
            continue
        if g.get("category") != "question":
            continue
        node_id = g.get("plan_node_id")
        body = latest_question_body_by_node.get(node_id, "")
        for question_key, verdict in answers.items():
            if question_key in body:
                await arbitrator.resolve_gate(g["gate_id"], verdict=verdict)
                break
