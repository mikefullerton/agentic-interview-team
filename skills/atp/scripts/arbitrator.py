#!/usr/bin/env python3
"""Arbitrator — communication conduit between pipeline participants.

Delegates all persistence to the storage-provider. Adds communication
semantics (session lifecycle, state transitions, message routing) on top.

Usage: arbitrator.py <resource> <action> [--flags]
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from storage_provider import dispatch


def main():
    if len(sys.argv) < 3:
        print("Usage: arbitrator.py <resource> <action> [flags]", file=sys.stderr)
        sys.exit(1)

    resource = sys.argv[1]
    action = sys.argv[2]
    flags = sys.argv[3:]

    backend = os.environ.get("STORAGE_PROVIDER_BACKEND", "markdown")
    dispatch(resource, action, flags, backend=backend)


if __name__ == "__main__":
    main()
