#!/usr/bin/env python3
# run_specialty_teams.py — Read specialty-team definitions for a specialist
#
# Reads the specialist's ## Manifest section, resolves each path to a
# specialty-team file, parses its frontmatter and body sections, and
# outputs a JSON array.
#
# Usage:
#   run_specialty_teams.py <specialist-file> [--mode <mode>]
#
# Output: JSON array of specialty-team definitions

import sys
import json
import argparse
from pathlib import Path


def parse_manifest_paths(specialist_file):
    """Extract paths from the ## Manifest section of a specialist file."""
    paths = []
    in_manifest = False

    with open(specialist_file) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## Manifest"):
                in_manifest = True
                continue
            if in_manifest and line.startswith("## "):
                break
            if in_manifest and line.startswith("- "):
                paths.append(line[2:])

    return paths


def parse_team_file(team_file):
    """Parse a specialty-team file and return its fields."""
    name = ""
    artifact = ""
    worker_focus = ""
    verify = ""

    # Parse frontmatter
    in_frontmatter = False
    front_count = 0
    body_lines = []

    with open(team_file) as f:
        lines = f.readlines()

    frontmatter_done = False
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line == "---" and not frontmatter_done:
            front_count += 1
            if front_count == 1:
                in_frontmatter = True
                i += 1
                continue
            elif front_count == 2:
                in_frontmatter = False
                frontmatter_done = True
                i += 1
                continue
        if in_frontmatter:
            if line.startswith("name:"):
                name = line[len("name:"):].strip()
            elif line.startswith("artifact:"):
                artifact = line[len("artifact:"):].strip()
        else:
            body_lines.append(line)
        i += 1

    # Parse body sections — capture only first non-empty line per section
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
        "name": name,
        "artifact": artifact,
        "worker_focus": worker_focus,
        "verify": verify,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: run_specialty_teams.py <specialist-file> [--mode <mode>]", file=sys.stderr)
        sys.exit(1)

    specialist_file = sys.argv[1]

    if not Path(specialist_file).is_file():
        print(f"ERROR: Specialist file not found: {specialist_file}", file=sys.stderr)
        sys.exit(1)

    # Resolve repo root from specialist file location
    repo_root = Path(specialist_file).resolve().parent.parent

    manifest_paths = parse_manifest_paths(specialist_file)

    if not manifest_paths:
        print(f"ERROR: No manifest entries found in {specialist_file}", file=sys.stderr)
        sys.exit(1)

    teams = []
    for team_path in manifest_paths:
        team_file = repo_root / team_path
        if not team_file.is_file():
            print(f"ERROR: Specialty-team file not found: {team_file}", file=sys.stderr)
            sys.exit(1)
        teams.append(parse_team_file(team_file))

    print(json.dumps(teams, indent=2))


if __name__ == "__main__":
    main()
