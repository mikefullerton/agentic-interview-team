#!/usr/bin/env python3
"""Unified storage-provider for the team-pipeline.

Single entry point for all data persistence. Backend-swappable via
STORAGE_PROVIDER_BACKEND env var (default: markdown).

Usage: storage_provider.py <resource> <action> [--flags]
"""
import importlib
import importlib.util
import os
import sys
from pathlib import Path


def dispatch(resource, action, flags, backend=None):
    """Dispatch a resource action to the configured backend."""
    if backend is None:
        backend = os.environ.get("STORAGE_PROVIDER_BACKEND", "markdown")

    module_name = resource.replace("-", "_")
    script_dir = Path(__file__).parent / "storage-provider" / backend
    module_path = script_dir / f"{module_name}.py"

    if not module_path.exists():
        print(f"Unknown resource: {resource}", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Resource modules read from sys.argv directly
    sys.argv = [str(module_path), action] + flags
    mod.main()


def main():
    if len(sys.argv) < 3:
        print("Usage: storage_provider.py <resource> <action> [flags]", file=sys.stderr)
        sys.exit(1)

    resource = sys.argv[1]
    action = sys.argv[2]
    flags = sys.argv[3:]

    dispatch(resource, action, flags)


if __name__ == "__main__":
    main()
