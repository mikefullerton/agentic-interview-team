#!/usr/bin/env python3
# run_specialty_teams.py — Read specialty-team and consulting-team definitions for a specialist
#
# Reads the specialist's ## Manifest and ## Consulting Teams sections,
# resolves each path, parses frontmatter and body sections, and outputs JSON.
#
# Usage:
#   run_specialty_teams.py <specialist-file>
#
# Output: JSON object with specialty_teams and consulting_teams arrays.
# If no ## Consulting Teams section exists, consulting_teams is empty.

import sys
import json
from pathlib import Path


def parse_section_paths(specialist_file, section_heading):
    """Extract paths from a named ## section of a specialist file."""
    paths = []
    in_section = False

    with open(specialist_file) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(f"## {section_heading}"):
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("- "):
                paths.append(line[2:])

    return paths


def parse_frontmatter(lines):
    """Parse YAML frontmatter from lines, return (fields_dict, body_start_index)."""
    fields = {}
    in_frontmatter = False
    front_count = 0
    body_start = 0
    current_list_key = ""

    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if stripped == "---":
            front_count += 1
            if front_count == 1:
                in_frontmatter = True
                continue
            elif front_count == 2:
                in_frontmatter = False
                body_start = i + 1
                break
        if in_frontmatter:
            if stripped.startswith("  - ") and current_list_key:
                fields[current_list_key].append(stripped.strip().lstrip("- ").strip())
                continue
            current_list_key = ""
            if stripped.startswith("name:"):
                fields["name"] = stripped[len("name:"):].strip()
            elif stripped.startswith("artifact:"):
                fields["artifact"] = stripped[len("artifact:"):].strip()
            elif stripped.startswith("type:"):
                fields["type"] = stripped[len("type:"):].strip()
            elif stripped.startswith("source:"):
                value = stripped[len("source:"):].strip()
                if value:
                    fields["source"] = [value]
                else:
                    fields["source"] = []
                    current_list_key = "source"

    return fields, body_start


def parse_team_file(team_file):
    """Parse a specialty-team file and return its fields."""
    with open(team_file) as f:
        lines = f.readlines()

    fields, body_start = parse_frontmatter(lines)
    body_lines = [l.rstrip("\n") for l in lines[body_start:]]

    worker_focus = ""
    verify = ""
    current_section = ""

    for line in body_lines:
        if line == "## Worker Focus":
            current_section = "focus"
            continue
        if line == "## Verify":
            current_section = "verify"
            continue
        if line.startswith("## "):
            current_section = ""
            continue
        if not line.strip():
            continue
        if current_section == "focus" and not worker_focus:
            worker_focus = line.strip()
        elif current_section == "verify" and not verify:
            verify = line.strip()

    return {
        "name": fields.get("name", ""),
        "artifact": fields.get("artifact", ""),
        "worker_focus": worker_focus,
        "verify": verify,
    }


def parse_consulting_team_file(team_file):
    """Parse a consulting-team file and return its fields."""
    with open(team_file) as f:
        lines = f.readlines()

    fields, body_start = parse_frontmatter(lines)
    body_lines = [l.rstrip("\n") for l in lines[body_start:]]

    consulting_focus = ""
    verify = ""
    current_section = ""

    for line in body_lines:
        if line == "## Consulting Focus":
            current_section = "focus"
            continue
        if line == "## Verify":
            current_section = "verify"
            continue
        if line.startswith("## "):
            current_section = ""
            continue
        if not line.strip():
            continue
        if current_section == "focus" and not consulting_focus:
            consulting_focus = line.strip()
        elif current_section == "verify" and not verify:
            verify = line.strip()

    return {
        "name": fields.get("name", ""),
        "type": fields.get("type", ""),
        "source": fields.get("source", []),
        "consulting_focus": consulting_focus,
        "verify": verify,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: run_specialty_teams.py <specialist-file>", file=sys.stderr)
        sys.exit(1)

    specialist_file = sys.argv[1]

    if not Path(specialist_file).is_file():
        print(f"ERROR: Specialist file not found: {specialist_file}", file=sys.stderr)
        sys.exit(1)

    # Resolve repo root from specialist file location
    repo_root = Path(specialist_file).resolve().parent.parent

    # Parse specialty teams
    manifest_paths = parse_section_paths(specialist_file, "Manifest")
    if not manifest_paths:
        print(f"ERROR: No manifest entries found in {specialist_file}", file=sys.stderr)
        sys.exit(1)

    specialty_teams = []
    for team_path in manifest_paths:
        team_file = repo_root / team_path
        if not team_file.is_file():
            print(f"ERROR: Specialty-team file not found: {team_file}", file=sys.stderr)
            sys.exit(1)
        specialty_teams.append(parse_team_file(team_file))

    # Parse consulting teams (optional section)
    consulting_paths = parse_section_paths(specialist_file, "Consulting Teams")
    consulting_teams = []
    for team_path in consulting_paths:
        team_file = repo_root / team_path
        if not team_file.is_file():
            print(f"ERROR: Consulting-team file not found: {team_file}", file=sys.stderr)
            sys.exit(1)
        consulting_teams.append(parse_consulting_team_file(team_file))

    output = {
        "specialty_teams": specialty_teams,
        "consulting_teams": consulting_teams,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
