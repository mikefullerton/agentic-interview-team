"""Parser pulls Task-tool invocations out of a stream-json event sequence."""
from __future__ import annotations

from services.conductor.dispatcher.stream_parser import SubagentStreamParser


def test_parser_emits_start_and_end_for_each_task_call():
    parser = SubagentStreamParser()
    events = [
        {"type": "tool_use", "id": "tu1", "name": "Task",
         "input": {"subagent_type": "speciality-worker",
                   "description": "work",
                   "prompt": "do stuff"}},
        {"type": "tool_result", "tool_use_id": "tu1",
         "content": [{"type": "text", "text": '{"output": "ok"}'}]},
        {"type": "tool_use", "id": "tu2", "name": "Task",
         "input": {"subagent_type": "speciality-verifier",
                   "description": "verify",
                   "prompt": "check"}},
        {"type": "tool_result", "tool_use_id": "tu2",
         "content": [{"type": "text",
                      "text": '{"verdict": "pass"}'}]},
    ]
    starts, ends = [], []
    for e in events:
        out = parser.ingest(e)
        starts.extend(out.starts)
        ends.extend(out.ends)

    assert [s.subagent_name for s in starts] == [
        "speciality-worker", "speciality-verifier",
    ]
    assert [e.tool_use_id for e in ends] == ["tu1", "tu2"]


def test_parser_ignores_non_task_tools():
    parser = SubagentStreamParser()
    out = parser.ingest({"type": "tool_use", "id": "x", "name": "Read",
                         "input": {"file_path": "/tmp/foo"}})
    assert out.starts == []
    assert out.ends == []


def test_tool_result_without_matching_start_is_dropped():
    parser = SubagentStreamParser()
    out = parser.ingest({"type": "tool_result", "tool_use_id": "ghost",
                         "content": []})
    assert out.ends == []
