#!/usr/bin/env python3
"""db-init — Create or migrate the dev-team shared database.
Usage: db_init.py
Idempotent — safe to call on every workflow startup.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import init_db, get_db_path


def main():
    init_db()
    print(get_db_path())


if __name__ == "__main__":
    main()
