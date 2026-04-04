#!/usr/bin/env python3
"""Project lifecycle for markdown project-storage."""
import json
import sys
from pathlib import Path
from _lib import (
    parse_flags, require_flag, project_dir, require_project,
    today_iso, json_output, json_build,
)


def init(flags):
    name = require_flag(flags, "name")
    description = require_flag(flags, "description")
    path = require_flag(flags, "path")

    d = project_dir(path)
    if d.is_dir():
        print(f"Project already exists at: {path}", file=sys.stderr)
        sys.exit(1)

    for subdir in ("schedule", "todos", "issues", "concerns", "dependencies", "decisions"):
        (d / subdir).mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": name,
        "description": description,
        "created": today_iso(),
        "modified": today_iso(),
        "cookbook_projects": [],
    }
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False))

    json_build(name=name, path=path)


def status(flags):
    project = require_flag(flags, "project")
    d = require_project(project)

    manifest = json.loads((d / "manifest.json").read_text())

    item_counts = {}
    for type_dir in ("schedule", "todos", "issues", "concerns", "dependencies", "decisions"):
        subdir = d / type_dir
        if subdir.is_dir():
            count = sum(1 for f in subdir.iterdir() if f.suffix == ".md" and f.is_file())
        else:
            count = 0
        item_counts[type_dir] = count

    manifest["item_counts"] = item_counts
    json_output(manifest)


def link_cookbook(flags):
    project = require_flag(flags, "project")
    path = require_flag(flags, "path")
    d = require_project(project)

    manifest_file = d / "manifest.json"
    manifest = json.loads(manifest_file.read_text())

    projects = manifest.get("cookbook_projects", [])
    if path not in projects:
        projects.append(path)
    manifest["cookbook_projects"] = projects
    manifest["modified"] = today_iso()
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False))

    json_build(project=project, cookbook_project=path)


def unlink_cookbook(flags):
    project = require_flag(flags, "project")
    path = require_flag(flags, "path")
    d = require_project(project)

    manifest_file = d / "manifest.json"
    manifest = json.loads(manifest_file.read_text())

    projects = manifest.get("cookbook_projects", [])
    projects = [p for p in projects if p != path]
    manifest["cookbook_projects"] = projects
    manifest["modified"] = today_iso()
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False))

    json_build(project=project, cookbook_project=path)


def main():
    if len(sys.argv) < 2:
        print("Usage: project.py <init|status|link-cookbook|unlink-cookbook> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "init": init,
        "status": status,
        "link-cookbook": link_cookbook,
        "unlink-cookbook": unlink_cookbook,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        print("Usage: project.py <init|status|link-cookbook|unlink-cookbook> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
