#!/usr/bin/env python3
"""Dependency CRUD for markdown project-storage."""
import sys
from _lib import (
    parse_flags, require_flag, require_project,
    next_id, slugify, today_iso, read_frontmatter, read_body,
    write_item, update_item, json_output, json_build,
)


def create(flags):
    project = require_flag(flags, "project")
    name = require_flag(flags, "name")
    description = require_flag(flags, "description")
    dep_type = require_flag(flags, "type")
    status = require_flag(flags, "status")

    d = require_project(project)
    dep_dir = d / "dependencies"
    dep_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("dependency", dep_dir)
    slug = slugify(name)
    file = dep_dir / f"{item_id}-{slug}.md"

    metadata = {
        "id": item_id,
        "name": name,
        "status": status,
        "type": dep_type,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    dep_dir = d / "dependencies"

    matches = sorted(dep_dir.glob(f"{item_id}-*.md")) if dep_dir.is_dir() else []
    if not matches:
        print(f"Dependency not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    dep_dir = d / "dependencies"
    dep_dir.mkdir(parents=True, exist_ok=True)

    status_filter = flags.get("status", "")
    type_filter = flags.get("type", "")

    result = []
    for f in sorted(dep_dir.glob("*.md")):
        if not f.is_file():
            continue
        data = read_frontmatter(f)
        if status_filter and data.get("status") != status_filter:
            continue
        if type_filter and data.get("type") != type_filter:
            continue
        result.append(data)

    json_output(result)


def update(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    dep_dir = d / "dependencies"

    matches = sorted(dep_dir.glob(f"{item_id}-*.md")) if dep_dir.is_dir() else []
    if not matches:
        print(f"Dependency not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("name"):
        updates["name"] = flags["name"]
    if flags.get("status"):
        updates["status"] = flags["status"]
    if flags.get("type"):
        updates["type"] = flags["type"]

    description = flags.get("description", "")
    if description:
        current = read_frontmatter(matches[0])
        current.update(updates)
        current["modified"] = today_iso()
        write_item(matches[0], description, current)
    else:
        update_item(matches[0], updates)

    json_build(id=item_id)


def delete(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    dep_dir = d / "dependencies"

    matches = sorted(dep_dir.glob(f"{item_id}-*.md")) if dep_dir.is_dir() else []
    if not matches:
        print(f"Dependency not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: dependency.py <create|get|list|update|delete> [flags]", file=sys.stderr)
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
        print("Usage: dependency.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
