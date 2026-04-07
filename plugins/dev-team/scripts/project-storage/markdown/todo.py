#!/usr/bin/env python3
"""Todo CRUD for markdown project-storage."""
import sys
from pathlib import Path
from project_store import (
    parse_flags, require_flag, require_project,
    next_id, slugify, today_iso, read_frontmatter, read_body,
    write_item, update_item, json_output, json_build,
)


def create(flags):
    project = require_flag(flags, "project")
    title = require_flag(flags, "title")
    description = require_flag(flags, "description")
    priority = require_flag(flags, "priority")
    status = require_flag(flags, "status")

    d = require_project(project)
    todo_dir = d / "todos"
    todo_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("todo", todo_dir)
    slug = slugify(title)
    file = todo_dir / f"{item_id}-{slug}.md"

    assignee = flags.get("assignee") or None
    milestone = flags.get("milestone") or None
    blocked_by = flags.get("blocked_by") or None

    metadata = {
        "id": item_id,
        "title": title,
        "status": status,
        "priority": priority,
        "assignee": assignee,
        "milestone": milestone,
        "blocked_by": blocked_by,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    todo_dir = d / "todos"

    matches = sorted(todo_dir.glob(f"{item_id}-*.md")) if todo_dir.is_dir() else []
    if not matches:
        print(f"Todo not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    todo_dir = d / "todos"
    todo_dir.mkdir(parents=True, exist_ok=True)

    status_filter = flags.get("status", "")
    priority_filter = flags.get("priority", "")
    milestone_filter = flags.get("milestone", "")

    result = []
    for f in sorted(todo_dir.glob("*.md")):
        if not f.is_file():
            continue
        data = read_frontmatter(f)
        if status_filter and data.get("status") != status_filter:
            continue
        if priority_filter and data.get("priority") != priority_filter:
            continue
        if milestone_filter and data.get("milestone") != milestone_filter:
            continue
        result.append(data)

    json_output(result)


def update(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    todo_dir = d / "todos"

    matches = sorted(todo_dir.glob(f"{item_id}-*.md")) if todo_dir.is_dir() else []
    if not matches:
        print(f"Todo not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("title"):
        updates["title"] = flags["title"]
    if flags.get("status"):
        updates["status"] = flags["status"]
    if flags.get("priority"):
        updates["priority"] = flags["priority"]
    if flags.get("assignee"):
        updates["assignee"] = flags["assignee"]
    if flags.get("milestone"):
        updates["milestone"] = flags["milestone"]
    if flags.get("blocked_by"):
        updates["blocked_by"] = flags["blocked_by"]

    update_item(matches[0], updates)
    json_build(id=item_id)


def delete(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    todo_dir = d / "todos"

    matches = sorted(todo_dir.glob(f"{item_id}-*.md")) if todo_dir.is_dir() else []
    if not matches:
        print(f"Todo not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: todo.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "get": get,
        "list": list_all,
        "update": update,
        "delete": delete,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        print("Usage: todo.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
