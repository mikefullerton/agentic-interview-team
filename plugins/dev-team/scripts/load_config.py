#!/usr/bin/env python3
# load_config.py — Load and migrate dev-team configuration
# Usage: load_config.py [--config <path>]
# Outputs: JSON config to stdout, errors to stderr
# Exit codes: 0 = success, 1 = config not found or invalid

import sys
import json
import os
import shutil
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default="")
    args, _ = parser.parse_known_args()

    home = Path.home()
    new_config = home / ".agentic-cookbook" / "dev-team" / "config.json"
    old_config = home / ".agentic-interviewer" / "config.json"

    config_path = Path(args.config) if args.config else new_config

    # Migrate from old location if needed
    if not config_path.exists() and old_config.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(old_config) as f:
            old_data = json.load(f)
        new_data = {
            "workspace_repo": old_data.get("interview_repo"),
            "cookbook_repo": old_data.get("cookbook_repo"),
            "user_name": old_data.get("user_name"),
            "authorized_repos": old_data.get("authorized_repos", []),
        }
        with open(config_path, "w") as f:
            json.dump(new_data, f, indent=2)
        print(f"Migrated config from {old_config} to {config_path}", file=sys.stderr)

    if not config_path.exists():
        print(f"Config not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Validate required fields
    required = ["workspace_repo", "cookbook_repo", "user_name"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print("Config missing required fields (workspace_repo, cookbook_repo, user_name)", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
