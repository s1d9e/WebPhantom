"""Chrome/Chromium browser artifact parser."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from webphantom.core.models import Artifact, ArtifactType, BrowserType
from webphantom.core.parser import ArtifactParser
from webphantom.core.wal_recovery import WALRecovery

logger = logging.getLogger(__name__)

# Chrome stores timestamps as microseconds since 1601-01-01
CHROME_EPOCH = datetime(1601, 1, 1)


def chrome_timestamp_to_datetime(chrome_ts: int) -> datetime:
    """Convert Chrome timestamp (microseconds since 1601) to datetime."""
    if chrome_ts == 0:
        return datetime.now()
    return CHROME_EPOCH + timedelta(microseconds=chrome_ts)


class ChromeParser:
    """Parse Chrome/Chromium browser artifacts."""

    def __init__(self, profile_path: Path) -> None:
        self.profile_path = profile_path
        self.parser: ArtifactParser | None = None
        self.wal: WALRecovery | None = None

    def parse_history(self) -> list[Artifact]:
        """Parse browsing history from Chrome's History database."""
        history_path = self.profile_path / "History"
        if not history_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(history_path)
        self.wal = WALRecovery(history_path)

        try:
            rows = self.parser.execute_query("""
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                ORDER BY last_visit_time DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.HISTORY,
                    browser=BrowserType.CHROME,
                    url=row["url"],
                    title=row.get("title", ""),
                    timestamp=chrome_timestamp_to_datetime(row["last_visit_time"]),
                    visit_count=row.get("visit_count", 1),
                    source_file=str(history_path),
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Chrome history: %s", e)

        if self.wal.has_wal:
            wal_artifacts = self._recover_wal_history(history_path)
            artifacts.extend(wal_artifacts)

        self.parser.close()
        return artifacts

    def parse_cookies(self) -> list[Artifact]:
        """Parse cookies from Chrome's Cookies database."""
        cookies_path = self.profile_path / "Cookies"
        if not cookies_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(cookies_path)

        try:
            rows = self.parser.execute_query("""
                SELECT host_key, name, path, expires_utc, is_secure, is_httponly
                FROM cookies
                ORDER BY expires_utc DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.COOKIE,
                    browser=BrowserType.CHROME,
                    url=f"{row['host_key']}{row['path']}",
                    title=row["name"],
                    source_file=str(cookies_path),
                    metadata={
                        "secure": str(row.get("is_secure", 0)),
                        "httponly": str(row.get("is_httponly", 0)),
                    },
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Chrome cookies: %s", e)

        self.parser.close()
        return artifacts

    def parse_favicons(self) -> list[Artifact]:
        """Parse favicons from Chrome's Favicons database."""
        favicons_path = self.profile_path / "Favicons"
        if not favicons_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(favicons_path)

        try:
            rows = self.parser.execute_query("""
                SELECT page_url, icon_url
                FROM favicons
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.FAVICON,
                    browser=BrowserType.CHROME,
                    url=row["page_url"],
                    title=row.get("icon_url", ""),
                    source_file=str(favicons_path),
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Chrome favicons: %s", e)

        self.parser.close()
        return artifacts

    def parse_downloads(self) -> list[Artifact]:
        """Parse download history from Chrome's History database."""
        history_path = self.profile_path / "History"
        if not history_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(history_path)

        try:
            rows = self.parser.execute_query("""
                SELECT target_path, start_time, end_time, total_bytes, url
                FROM downloads
                ORDER BY start_time DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.DOWNLOAD,
                    browser=BrowserType.CHROME,
                    url=row.get("url", ""),
                    title=row.get("target_path", ""),
                    timestamp=chrome_timestamp_to_datetime(row.get("start_time", 0)),
                    source_file=str(history_path),
                    metadata={
                        "total_bytes": str(row.get("total_bytes", 0)),
                    },
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Chrome downloads: %s", e)

        self.parser.close()
        return artifacts

    def _recover_wal_history(self, db_path: Path) -> list[Artifact]:
        """Recover deleted history entries from WAL file."""
        artifacts: list[Artifact] = []

        if not self.wal:
            return artifacts

        try:
            wal_recovered = self.wal.get_wal_artifacts(
                "urls", ["url", "title", "last_visit_time"]
            )

            for row in wal_recovered:
                if "url" in row:
                    artifact = Artifact(
                        artifact_type=ArtifactType.WAL,
                        browser=BrowserType.CHROME,
                        url=row["url"],
                        title=row.get("title", ""),
                        from_wal=True,
                        source_file=str(db_path) + "-wal",
                    )
                    artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to recover WAL history: %s", e)

        return artifacts

    def parse_all(self) -> list[Artifact]:
        """Parse all available Chrome artifacts."""
        artifacts: list[Artifact] = []
        artifacts.extend(self.parse_history())
        artifacts.extend(self.parse_cookies())
        artifacts.extend(self.parse_favicons())
        artifacts.extend(self.parse_downloads())
        return artifacts
