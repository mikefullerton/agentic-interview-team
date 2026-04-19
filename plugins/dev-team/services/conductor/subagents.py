"""Load generic speciality subagent definitions from disk.

The parent specialist dispatches these via the Task tool. Topic-specific
content (worker_focus, verify criteria) flows in as Task input at call
time — the subagent prompts stay generic.
"""
from __future__ import annotations

from pathlib import Path

from .dispatcher import AgentDefinition
from .team_loader import _parse_frontmatter

SUBAGENT_DIR = Path(__file__).resolve().parents[2] / "subagents"


def load_generic_subagents() -> list[AgentDefinition]:
    defs: list[AgentDefinition] = []
    for md in sorted(SUBAGENT_DIR.glob("*.md")):
        text = md.read_text()
        fm, body = _parse_frontmatter(text)
        name = fm.get("name") or md.stem
        tools_raw = fm.get("tools", "") or ""
        if "\n" in tools_raw:
            tools = [t.strip(" -") for t in tools_raw.splitlines() if t.strip(" -")]
        else:
            tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
        defs.append(AgentDefinition(
            name=name, prompt=body.strip(),
            allowed_tools=tools,
        ))
    return defs
