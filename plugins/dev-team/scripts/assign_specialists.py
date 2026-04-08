#!/usr/bin/env python3
# assign_specialists.py — Determine specialist assignment for a recipe
# Usage: assign_specialists.py <recipe-path> [--platforms '<json-array>'] [--tier-order]
# Outputs: Newline-separated specialist domains to stdout
# With --tier-order: output is sorted by build tier

import sys
import json
import os
import re
import argparse
from pathlib import Path


def parse_frontmatter_domain(recipe_path):
    """Extract domain from recipe frontmatter scope field."""
    in_frontmatter = False
    front_count = 0
    with open(recipe_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "---":
                front_count += 1
                if front_count == 1:
                    in_frontmatter = True
                elif front_count == 2:
                    break
                continue
            if in_frontmatter and line.startswith("domain: "):
                # Matches: sub(/^domain: .*recipes\//, ""); sub(/\/[^\/]*$/, ""); gsub(/\//, ".")
                val = line[len("domain: "):]
                # Remove up to and including "recipes/"
                idx = val.find("recipes/")
                if idx != -1:
                    val = val[idx + len("recipes/"):]
                # Remove last path component
                idx = val.rfind("/")
                if idx != -1:
                    val = val[:idx]
                # Replace slashes with dots
                val = val.replace("/", ".")
                return val
    return ""


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("recipe_path")
    parser.add_argument("--platforms", default="[]")
    parser.add_argument("--tier-order", action="store_true")
    args, _ = parser.parse_known_args()

    recipe_path = args.recipe_path
    platforms_json = args.platforms
    tier_order = args.tier_order

    # Locate mapping file
    script_dir = Path(__file__).parent
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", str(script_dir / ".."))
    mapping_path = Path(plugin_root) / "docs" / "research" / "specialist-assignment.json"

    with open(mapping_path) as f:
        mapping = json.load(f)

    specialists = []

    # 1. Category mapping
    recipe_domain = parse_frontmatter_domain(recipe_path)
    if recipe_domain:
        category = "recipe." + recipe_domain.split(".")[0]
        category_mappings = mapping.get("category-mappings", {})
        for key, values in category_mappings.items():
            if category.startswith(key):
                specialists.extend(values)

    # 2. Content keyword scan
    with open(recipe_path) as f:
        recipe_content = f.read()

    content_keywords = mapping.get("content-keywords", {})
    for keyword, specialist in content_keywords.items():
        if re.search(re.escape(keyword), recipe_content, re.IGNORECASE):
            if specialist and specialist != "null":
                specialists.append(specialist)

    # 3. Platform specialists
    try:
        platforms = json.loads(platforms_json)
    except json.JSONDecodeError:
        platforms = []

    platform_mappings = mapping.get("platform-mappings", {})
    for plat in platforms:
        for s in platform_mappings.get(plat, []):
            if s and s != "null":
                specialists.append(s)

    # 4. Universal specialists (assigned to every recipe)
    universal = mapping.get("universal-specialists", [])
    specialists.extend(universal)

    # Deduplicate
    if not specialists:
        sys.exit(0)

    unique = sorted(set(specialists))

    if tier_order:
        tier_order_map = mapping.get("tier-order", [])
        # tier-order is a list; find index of each specialist
        def tier_index(s):
            try:
                return tier_order_map.index(s)
            except ValueError:
                return 999

        unique = sorted(unique, key=tier_index)

    print("\n".join(unique))


if __name__ == "__main__":
    main()
