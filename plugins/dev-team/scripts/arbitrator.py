#!/usr/bin/env python3
"""Unified data exchange API for dev-team pipeline."""
import importlib
import importlib.util
import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: arbitrator.py <resource> <action> [flags]", file=sys.stderr)
        sys.exit(1)

    backend = os.environ.get("ARBITRATOR_BACKEND", "markdown")
    resource = sys.argv[1]
    action = sys.argv[2]
    flags = sys.argv[3:]

    # Map hyphenated resource names to Python module names
    module_name = resource.replace("-", "_")
    script_dir = Path(__file__).parent / "arbitrator" / backend
    module_path = script_dir / f"{module_name}.py"

    if not module_path.exists():
        print(f"Unknown resource: {resource}", file=sys.stderr)
        sys.exit(1)

    # Add backend dir to path so module can import _lib
    sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Call main with action + flags
    sys.argv = [str(module_path), action] + flags
    mod.main()

if __name__ == "__main__":
    main()
