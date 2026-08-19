"""Firefox browser artifact parser."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from webphantom.core.models import Artifact, ArtifactType, BrowserType
from webphantom.core.parser import ArtifactParser
from webphantom.core.wal_recovery import WALRecovery

logger = logging.getLogger(__name__)

# Firefox stores timestamps as microseconds since 1970-01-01
FIREFOX_EPOCH = datetime(1970, 1, 1)


def firefox_timestamp_to_datetime(firefox_ts: int) -> datetime:
    """Convert Firefox timestamp (microseconds since 1970) to datetime."""
    if firefox_ts == 0:
        return datetime.now()
    return FIREFOX_EPOCH + timedelta(microseconds=firefox_ts)


class FirefoxParser:
    """Parse Firefox browser artifacts."""

    def __init__(self, profile_path: Path) -> None:
        self.profile_path = profile_path
        self.parser: ArtifactParser | None = None
        self.wal: WALRecovery | None = None

    def parse_history(self) -> list[Artifact]:
        """Parse browsing history from Firefox's places.sqlite."""
        places_path = self.profile_path / "places.sqlite"
        if not places_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(places_path)
        self.wal = WALRecovery(places_path)

        try:
            rows = self.parser.execute_query("""
                SELECT p.url, p.title, p.visit_count, p.last_visit_date
                FROM moz_places p
                WHERE p.visit_count > 0
                ORDER BY p.last_visit_date DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.HISTORY,
                    browser=BrowserType.FIREFOX,
                    url=row["url"],
                    title=row.get("title", ""),
                    timestamp=firefox_timestamp_to_datetime(row.get("last_visit_date", 0)),
                    visit_count=row.get("visit_count", 1),
                    source_file=str(places_path),
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Firefox history: %s", e)

        if self.wal.has_wal:
            wal_artifacts = self._recover_wal_history(places_path)
            artifacts.extend(wal_artifacts)

        self.parser.close()
        return artifacts

    def parse_cookies(self) -> list[Artifact]:
        """Parse cookies from Firefox's cookies.sqlite."""
        cookies_path = self.profile_path / "cookies.sqlite"
        if not cookies_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(cookies_path)

        try:
            rows = self.parser.execute_query("""
                SELECT host, name, path, expiry, isSecure, isHttpOnly
                FROM moz_cookies
                ORDER BY expiry DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.COOKIE,
                    browser=BrowserType.FIREFOX,
                    url=f"{row['host']}{row['path']}",
                    title=row["name"],
                    source_file=str(cookies_path),
                    metadata={
                        "secure": str(row.get("isSecure", 0)),
                        "httponly": str(row.get("isHttpOnly", 0)),
                    },
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Firefox cookies: %s", e)

        self.parser.close()
        return artifacts

    def parse_favicons(self) -> list[Artifact]:
        """Parse favicons from Firefox's favicons.sqlite."""
        favicons_path = self.profile_path / "favicons.sqlite"
        if not favicons_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(favicons_path)

        try:
            rows = self.parser.execute_query("""
                SELECT page_url, icon_url
                FROM moz_favicons
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.FAVICON,
                    browser=BrowserType.FIREFOX,
                    url=row["page_url"],
                    title=row.get("icon_url", ""),
                    source_file=str(favicons_path),
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Firefox favicons: %s", e)

        self.parser.close()
        return artifacts

    def parse_downloads(self) -> list[Artifact]:
        """Parse download history from Firefox's places.sqlite."""
        places_path = self.profile_path / "places.sqlite"
        if not places_path.exists():
            return []

        artifacts: list[Artifact] = []
        self.parser = ArtifactParser(places_path)

        try:
            rows = self.parser.execute_query("""
                SELECT ann.target, ann.dateAdded, ann.content
                FROM moz_annos ann
                JOIN moz_anno_names n ON ann.anno_attribute_id = n.id
                WHERE n.name = 'downloads/destinationFileURI'
                ORDER BY ann.dateAdded DESC
            """)

            for row in rows:
                artifact = Artifact(
                    artifact_type=ArtifactType.DOWNLOAD,
                    browser=BrowserType.FIREFOX,
                    url=row.get("target", ""),
                    timestamp=firefox_timestamp_to_datetime(row.get("dateAdded", 0)),
                    source_file=str(places_path),
                )
                artifacts.append(artifact)

        except Exception as e:
            logger.warning("Failed to parse Firefox downloads: %s", e)

        self.parser.close()
        return artifacts

    def _recover_wal_history(self, db_path: Path) -> list[Artifact]:
        """Recover deleted history entries from WAL file."""
        artifacts: list[Artifact] = []

        if not self.wal:
            return artifacts

        try:
            wal_recovered = self.wal.get_wal_artifacts(
                "moz_places", ["url", "title", "last_visit_date"]
            )

            for row in wal_recovered:
                if "url" in row:
                    artifact = Artifact(
                        artifact_type=ArtifactType.WAL,
                        browser=BrowserType.FIREFOX,
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
        """Parse all available Firefox artifacts."""
        artifacts: list[Artifact] = []
        artifacts.extend(self.parse_history())
        artifacts.extend(self.parse_cookies())
        artifacts.extend(self.parse_favicons())
        artifacts.extend(self.parse_downloads())
        return artifacts
