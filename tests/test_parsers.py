"""Integration test with mock browser data."""

import sqlite3
import tempfile
from pathlib import Path
from webphantom.browsers.chrome import ChromeParser
from webphantom.browsers.firefox import FirefoxParser
from webphantom.core.models import BrowserType, ArtifactType


def create_mock_chrome_history(db_path: Path) -> None:
    """Create a mock Chrome History database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            visit_count INTEGER DEFAULT 1,
            last_visit_time INTEGER DEFAULT 13200000000000000
        )
    """)
    conn.execute("""
        INSERT INTO urls (url, title, visit_count, last_visit_time)
        VALUES 
            ('https://github.com', 'GitHub', 5, 13200000000000000),
            ('https://example.com', 'Example', 1, 13200000000000000)
    """)
    conn.commit()
    conn.close()


def create_mock_firefox_history(db_path: Path) -> None:
    """Create a mock Firefox places.sqlite database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE moz_places (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            visit_count INTEGER DEFAULT 1,
            last_visit_date INTEGER DEFAULT 1700000000000000
        )
    """)
    conn.execute("""
        INSERT INTO moz_places (url, title, visit_count, last_visit_date)
        VALUES 
            ('https://mozilla.org', 'Mozilla', 3, 1700000000000000),
            ('https://firefox.com', 'Firefox', 1, 1700000000000000)
    """)
    conn.commit()
    conn.close()


def test_chrome_parsing():
    """Test Chrome parser with mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile_path = Path(tmpdir)
        db_path = profile_path / "History"
        create_mock_chrome_history(db_path)

        parser = ChromeParser(profile_path)
        artifacts = parser.parse_history()

        assert len(artifacts) == 2
        assert artifacts[0].browser == BrowserType.CHROME
        assert artifacts[0].artifact_type == ArtifactType.HISTORY
        assert "github.com" in artifacts[0].url


def test_firefox_parsing():
    """Test Firefox parser with mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        profile_path = Path(tmpdir)
        db_path = profile_path / "places.sqlite"
        create_mock_firefox_history(db_path)

        parser = FirefoxParser(profile_path)
        artifacts = parser.parse_history()

        assert len(artifacts) == 2
        assert artifacts[0].browser == BrowserType.FIREFOX
        assert artifacts[0].artifact_type == ArtifactType.HISTORY
        assert "mozilla.org" in artifacts[0].url
