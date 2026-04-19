"""Subagent loader returns one AgentDefinition per markdown file."""
from __future__ import annotations

from services.conductor.subagents import load_generic_subagents


def test_loader_returns_worker_and_verifier():
    subs = load_generic_subagents()
    names = {s.name for s in subs}
    assert names == {"speciality-worker", "speciality-verifier"}


def test_worker_prompt_mentions_focus_and_structured_output():
    subs = {s.name: s for s in load_generic_subagents()}
    body = subs["speciality-worker"].prompt
    assert "focus" in body.lower()
    assert "structured" in body.lower() or "json" in body.lower()


def test_verifier_prompt_asks_for_verdict():
    subs = {s.name: s for s in load_generic_subagents()}
    body = subs["speciality-verifier"].prompt
    assert "verdict" in body.lower()
