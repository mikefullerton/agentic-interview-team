"""Read-only connection to the dev-team shared database."""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.path.join(
    Path.home(), ".agentic-cookbook", "dev-team", "dev-team.db"
)


def get_db_path():
    return os.environ.get("DEVTEAM_DB", DEFAULT_DB_PATH)


def connect(db_path=None):
    """Open a read-only connection to the dev-team database."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA query_only=ON")
    return conn


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)
