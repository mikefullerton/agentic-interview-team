"""Parse `claude -p` stream-json for subagent Task invocations.

The specialist's stream emits Anthropic-API-style tool_use / tool_result
events. When name == "Task", the payload represents a Task-tool
subagent invocation. This parser tracks those events so the caller can
open a child `dispatch` row on start and close it on result.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubagentStart:
    tool_use_id: str
    subagent_name: str
    description: str
    prompt: str


@dataclass
class SubagentEnd:
    tool_use_id: str
    output_text: str


@dataclass
class ParseStep:
    starts: list[SubagentStart] = field(default_factory=list)
    ends: list[SubagentEnd] = field(default_factory=list)


class SubagentStreamParser:
    def __init__(self) -> None:
        self._open: dict[str, SubagentStart] = {}

    def ingest(self, event: dict) -> ParseStep:
        step = ParseStep()
        etype = event.get("type")
        if etype == "tool_use" and event.get("name") == "Task":
            payload = event.get("input") or {}
            start = SubagentStart(
                tool_use_id=event.get("id", ""),
                subagent_name=payload.get("subagent_type", ""),
                description=payload.get("description", ""),
                prompt=payload.get("prompt", ""),
            )
            self._open[start.tool_use_id] = start
            step.starts.append(start)
        elif etype == "tool_result":
            tu_id = event.get("tool_use_id", "")
            if tu_id in self._open:
                text = _extract_text(event.get("content"))
                step.ends.append(SubagentEnd(tool_use_id=tu_id, output_text=text))
                self._open.pop(tu_id, None)
        return step


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(part.get("text", ""))
        return "".join(chunks)
    return ""
