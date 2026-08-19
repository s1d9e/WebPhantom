"""Core artifact parsing engine for WebPhantom."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ArtifactParser:
    """Parse browser artifacts from SQLite databases."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Open a read-only connection to the SQLite database."""
        if self._conn is None:
            uri = f"file:{self.db_path.as_posix()}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        conn = self.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def get_tables(self) -> list[str]:
        """List all tables in the database."""
        conn = self.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def execute_query(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        conn = self.connect()
        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def read_raw_page(self, page_number: int, page_size: int = 4096) -> bytes:
        """Read a raw page from the SQLite database."""
        with open(self.db_path, "rb") as f:
            f.seek(page_number * page_size)
            return f.read(page_size)
