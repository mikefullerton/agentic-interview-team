#!/usr/bin/env python3
# version_check.py — Compare running version against installed SKILL.md
# Usage: version_check.py <skill-dir> <running-version>
# Outputs: Warning to stderr if versions differ, nothing if they match

import sys
from pathlib import Path


def parse_frontmatter_version(skill_md_path):
    """Extract version from SKILL.md frontmatter."""
    in_frontmatter = False
    front_count = 0
    with open(skill_md_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "---":
                front_count += 1
                if front_count == 1:
                    in_frontmatter = True
                elif front_count == 2:
                    break
                continue
            if in_frontmatter and line.startswith("version: "):
                return line[len("version: "):].strip()
    return ""


def main():
    if len(sys.argv) < 3:
        sys.exit(0)

    skill_dir = sys.argv[1]
    running_version = sys.argv[2]

    skill_md = Path(skill_dir) / "SKILL.md"
    if not skill_md.exists():
        sys.exit(0)

    installed_version = parse_frontmatter_version(skill_md)

    if installed_version and installed_version != running_version:
        print(
            f"Warning: This skill is running v{running_version} but v{installed_version} is installed. "
            "Restart the session to use the latest version.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
