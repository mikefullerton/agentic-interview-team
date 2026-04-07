"""Shared helpers for the markdown project-storage backend."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR_NAME = ".dev-team-project"


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:40]


def project_dir(project_path: str) -> Path:
    return Path(project_path) / PROJECT_DIR_NAME


def require_project(project_path: str) -> Path:
    d = project_dir(project_path)
    if not d.is_dir():
        print(f"No dev-team project at: {project_path}", file=sys.stderr)
        sys.exit(1)
    return d


def next_id(item_type: str, directory: Path) -> str:
    """Return next ID e.g. 'todo-0001'."""
    directory.mkdir(parents=True, exist_ok=True)
    count = sum(1 for f in directory.iterdir() if f.suffix == ".md" and f.is_file())
    return f"{item_type}-{count + 1:04d}"


def read_frontmatter(file: Path) -> dict:
    """Parse YAML frontmatter from a markdown file into a dict."""
    text = file.read_text()
    lines = text.splitlines()
    in_frontmatter = False
    yaml_lines = []
    for line in lines:
        if line == "---":
            if in_frontmatter:
                break
            else:
                in_frontmatter = True
                continue
        if in_frontmatter:
            yaml_lines.append(line)

    result = {}
    for line in yaml_lines:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)", line)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).rstrip()
        if val == "null" or val == "":
            result[key] = None
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            if inner.strip() == "":
                result[key] = []
            else:
                result[key] = [item.strip() for item in inner.split(",")]
        else:
            result[key] = val
    return result


def read_body(file: Path) -> str:
    """Return everything after the second --- delimiter."""
    text = file.read_text()
    lines = text.splitlines()
    found_first = False
    past_frontmatter = False
    body_lines = []
    for line in lines:
        if line == "---":
            if found_first:
                past_frontmatter = True
                continue
            else:
                found_first = True
                continue
        if past_frontmatter:
            body_lines.append(line)
    return "\n".join(body_lines)


def _format_value(val) -> str:
    """Format a Python value as a YAML scalar."""
    if val is None:
        return "null"
    if isinstance(val, list):
        if not val:
            return "[]"
        return "[" + ", ".join(str(item) for item in val) + "]"
    return str(val)


def write_item(file: Path, body: str, metadata: dict) -> None:
    """Write a markdown file with YAML frontmatter."""
    lines = ["---"]
    for key, val in metadata.items():
        lines.append(f"{key}: {_format_value(val)}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    file.write_text("\n".join(lines) + "\n")


def update_item(file: Path, updates: dict) -> None:
    """Read existing file, merge updates, add modified date, rewrite."""
    current = read_frontmatter(file)
    body = read_body(file)
    current.update(updates)
    current["modified"] = today_iso()
    write_item(file, body, current)


def parse_flags(argv: list) -> dict:
    """Parse --flag value pairs from argv into a dict."""
    flag_map = {
        "--project": "project",
        "--name": "name",
        "--description": "description",
        "--path": "path",
        "--id": "id",
        "--title": "title",
        "--status": "status",
        "--priority": "priority",
        "--severity": "severity",
        "--assignee": "assignee",
        "--milestone": "milestone",
        "--blocked-by": "blocked_by",
        "--target-date": "target_date",
        "--dependencies": "dependencies",
        "--source": "source",
        "--related-findings": "related_findings",
        "--raised-by": "raised_by",
        "--related-to": "related_to",
        "--type": "type",
        "--rationale": "rationale",
        "--alternatives": "alternatives",
        "--made-by": "made_by",
        "--date": "date",
    }
    flags = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in flag_map and i + 1 < len(argv):
            flags[flag_map[arg]] = argv[i + 1]
            i += 2
        else:
            i += 1
    return flags


def require_flag(flags: dict, name: str) -> str:
    """Require a flag is present and non-empty."""
    val = flags.get(name, "")
    if not val:
        print(f"Missing required flag: --{name.replace('_', '-')}", file=sys.stderr)
        sys.exit(1)
    return val


def json_output(obj) -> None:
    """Print a JSON object to stdout."""
    print(json.dumps(obj, ensure_ascii=False))


def json_build(**kwargs) -> None:
    """Build and print a JSON object from kwargs."""
    print(json.dumps(kwargs, ensure_ascii=False))
