"""Data models for WebPhantom artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class BrowserType(Enum):
    """Supported browser types."""

    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    BRAVE = "brave"
    UNKNOWN = "unknown"


class ArtifactType(Enum):
    """Types of browser artifacts."""

    HISTORY = "history"
    FAVICON = "favicon"
    COOKIE = "cookie"
    DOWNLOAD = "download"
    SESSION = "session"
    INDEXED_DB = "indexed_db"
    LOCAL_STORAGE = "local_storage"
    SESSION_STORAGE = "session_storage"
    DNS = "dns"
    WAL = "wal"
    GPU_CACHE = "gpu_cache"


@dataclass
class Artifact:
    """A single browser artifact."""

    artifact_type: ArtifactType
    browser: BrowserType
    url: str
    title: str = ""
    timestamp: datetime | None = None
    visit_count: int = 0
    from_wal: bool = False
    source_file: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str | int | bool]:
        """Convert artifact to dictionary."""
        return {
            "type": self.artifact_type.value,
            "browser": self.browser.value,
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "visit_count": self.visit_count,
            "from_wal": self.from_wal,
            "source": self.source_file,
        }


@dataclass
class BrowserProfile:
    """Detected browser profile."""

    browser: BrowserType
    profile_path: Path
    name: str = "Default"
    os_type: str = "linux"

    @property
    def history_db(self) -> Path | None:
        """Path to the History SQLite database."""
        candidates = [
            self.profile_path / "History",
            self.profile_path / "places.sqlite",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @property
    def cookies_db(self) -> Path | None:
        """Path to the Cookies SQLite database."""
        candidates = [
            self.profile_path / "Cookies",
            self.profile_path / "cookies.sqlite",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @property
    def favicons_db(self) -> Path | None:
        """Path to the Favicons SQLite database."""
        candidates = [
            self.profile_path / "Favicons",
            self.profile_path / "favicons.sqlite",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None


@dataclass
class ScanResult:
    """Result of a browser artifact scan."""

    artifacts: list[Artifact] = field(default_factory=list)
    browsers_found: list[BrowserType] = field(default_factory=list)
    profiles_scanned: int = 0
    wal_files_recovered: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_artifacts(self) -> int:
        return len(self.artifacts)

    def timeline(self) -> list[Artifact]:
        """Return artifacts sorted by timestamp."""
        return sorted(
            [a for a in self.artifacts if a.timestamp is not None],
            key=lambda a: a.timestamp,  # type: ignore
        )
