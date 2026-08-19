"""Tests for WAL recovery engine."""

import sqlite3
import tempfile
from pathlib import Path
from webphantom.core.wal_recovery import WALRecovery, _sanitize_table_name


def test_sanitize_table_name_valid():
    """Test valid table names pass validation."""
    assert _sanitize_table_name("urls") == "urls"
    assert _sanitize_table_name("moz_places") == "moz_places"
    assert _sanitize_table_name("table123") == "table123"


def test_sanitize_table_name_invalid():
    """Test invalid table names are rejected."""
    import pytest
    with pytest.raises(ValueError):
        _sanitize_table_name("urls; DROP TABLE users;")
    with pytest.raises(ValueError):
        _sanitize_table_name("table' OR '1'='1")
    with pytest.raises(ValueError):
        _sanitize_table_name("123table")


def test_wal_recovery_no_wal():
    """Test WAL recovery with no WAL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        conn.commit()
        conn.close()
        
        wal = WALRecovery(db_path)
        assert not wal.has_wal
        assert not wal.has_journal
        
        result = wal.recover_deleted_rows("test")
        assert result == []


def test_wal_recovery_with_wal():
    """Test WAL recovery with existing WAL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT)")
        conn.execute("INSERT INTO urls (url) VALUES ('https://example.com')")
        conn.commit()
        conn.close()
        
        wal_path = Path(str(db_path) + "-wal")
        wal_path.write_bytes(b"test wal data")
        
        wal = WALRecovery(db_path)
        assert wal.has_wal
        
        result = wal.recover_deleted_rows("urls")
        assert isinstance(result, list)


def test_wal_header_reading():
    """Test WAL header reading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()
        
        wal_path = Path(str(db_path) + "-wal")
        # Create a minimal WAL header (32 bytes)
        header = bytes(32)
        wal_path.write_bytes(header)
        
        wal = WALRecovery(db_path)
        assert wal.has_wal
        
        info = wal.read_wal_header()
        assert "magic" in info
        assert "page_size" in info
        assert "checkpoint_seq" in info
