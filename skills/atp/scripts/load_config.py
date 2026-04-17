#!/usr/bin/env python3
# load_config.py — Load team-pipeline configuration
# Usage: load_config.py --config <path>
# Outputs: JSON config to stdout, errors to stderr
# Exit codes: 0 = success, 1 = config not found or invalid

import sys
import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", required=True)
    args, _ = parser.parse_known_args()

    config_path = Path(args.config)

    if not config_path.exists():
        print(f"Config not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Validate only team-pipeline required fields
    required = ["team_name", "user_name", "data_dir"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print(f"Config missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
