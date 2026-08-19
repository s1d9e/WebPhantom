"""WAL (Write-Ahead Logging) journal recovery engine.

This module recovers deleted or modified entries from SQLite WAL files.
When browsers modify their history/cookies, the old data often remains
in the WAL file until it's checkpointed.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

from webphantom.core.parser import ArtifactParser

logger = logging.getLogger(__name__)


def _sanitize_table_name(table_name: str) -> str:
    """Validate and sanitize a table name to prevent SQL injection.

    Only allows alphanumeric characters and underscores.
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name


class WALRecovery:
    """Recover data from SQLite WAL journal files."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.wal_path = Path(str(db_path) + "-wal")
        self.journal_path = Path(str(db_path) + "-journal")
        self.parser = ArtifactParser(db_path)

    @property
    def has_wal(self) -> bool:
        """Check if a WAL file exists for this database."""
        return self.wal_path.exists()

    @property
    def has_journal(self) -> bool:
        """Check if a journal file exists for this database."""
        return self.journal_path.exists()

    def read_wal_header(self) -> dict[str, Any]:
        """Read and parse the WAL file header."""
        if not self.has_wal:
            return {}

        with open(self.wal_path, "rb") as f:
            header = f.read(32)

        if len(header) < 32:
            return {}

        magic = int.from_bytes(header[0:4], "big")
        return {
            "magic": magic,
            "is_wal2": magic == 0x377F0682 or magic == 0x377F0683,
            "page_size": int.from_bytes(header[8:10], "big"),
            "checkpoint_seq": int.from_bytes(header[12:16], "big"),
        }

    def recover_deleted_rows(self, table_name: str) -> list[dict[str, Any]]:
        """Recover deleted rows by scanning WAL for old page data.

        This is a simplified approach that reads WAL frames and attempts
        to extract any recoverable data.
        """
        if not self.has_wal:
            return []

        table_name = _sanitize_table_name(table_name)
        recovered: list[dict[str, Any]] = []

        try:
            conn = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            current_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()

            with open(self.wal_path, "rb") as f:
                wal_data = f.read()

            page_size = 4096
            header_size = 32
            frame_size = 24 + page_size
            num_frames = (len(wal_data) - header_size) // frame_size

            for i in range(num_frames):
                frame_offset = header_size + (i * frame_size)
                if frame_offset + frame_size > len(wal_data):
                    break

                frame_data = wal_data[frame_offset + 24: frame_offset + 24 + page_size]

                if b"\x00" * 64 not in frame_data[:256]:
                    text_chunks = self._extract_text_from_page(frame_data)
                    for chunk in text_chunks:
                        if chunk and len(chunk) > 10:
                            for row in current_data:
                                if chunk in str(row.values()):
                                    recovered.append({
                                        **row,
                                        "_recovered_from": "wal",
                                        "_wal_frame": i,
                                    })

        except Exception as e:
            logger.warning("Failed to recover deleted rows: %s", e)

        return recovered

    def _extract_text_from_page(self, page_data: bytes) -> list[str]:
        """Extract readable text strings from a raw page."""
        strings: list[str] = []
        current: list[int] = []

        for byte in page_data:
            if 32 <= byte <= 126:
                current.append(byte)
            else:
                if len(current) >= 4:
                    strings.append(bytes(current).decode("ascii", errors="ignore"))
                current = []

        if len(current) >= 4:
            strings.append(bytes(current).decode("ascii", errors="ignore"))

        return strings

    def get_wal_artifacts(self, table_name: str, columns: list[str]) -> list[dict[str, Any]]:
        """Attempt to extract artifacts from WAL file directly.

        Uses a heuristic approach: if data exists in WAL but not in main DB,
        it was likely deleted or modified.
        """
        if not self.has_wal:
            return []

        table_name = _sanitize_table_name(table_name)
        artifacts: list[dict[str, Any]] = []

        try:
            conn = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row

            current_rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
            current_set = {tuple(row) for row in current_rows}
            conn.close()

            with open(self.wal_path, "rb") as f:
                wal_data = f.read()

            for byte_offset in range(0, len(wal_data) - 100):
                urls = self._extract_urls_from_region(wal_data, byte_offset)
                for url in urls:
                    is_in_current = False
                    for row in current_set:
                        if url.encode() in b"|".join(str(v).encode() for v in row):
                            is_in_current = True
                            break

                    if not is_in_current:
                        artifacts.append({
                            "url": url,
                            "_recovered_from": "wal",
                            "_wal_offset": byte_offset,
                        })

        except Exception as e:
            logger.warning("Failed to get WAL artifacts: %s", e)

        return artifacts

    def _extract_urls_from_region(self, data: bytes, offset: int) -> list[str]:
        """Extract URL-like strings from a data region."""
        urls: list[str] = []

        region = data[offset: offset + 2048]

        text_parts = region.split(b"\x00")
        for part in text_parts:
            try:
                text = part.decode("utf-8", errors="ignore")
                if text.startswith(("http://", "https://")) and len(text) < 2048:
                    urls.append(text)
            except Exception:
                continue

        return urls
