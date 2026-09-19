"""SQLite connection handling and first-run schema creation."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/shifts.db")
IN_MEMORY = ":memory:"

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the database, creating the file and schema if needed.

    Pass ``IN_MEMORY`` for a throwaway database, as the tests do.
    """
    if db_path != IN_MEMORY:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create any tables and indexes the database is missing."""
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
