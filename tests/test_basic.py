"""Basic tests for WebPhantom."""

from pathlib import Path
from webphantom.core.models import BrowserType, ArtifactType, Artifact, BrowserProfile, ScanResult
from webphantom.core.detector import detect_os


def test_browser_type_enum():
    """Test BrowserType enum values."""
    assert BrowserType.CHROME.value == "chrome"
    assert BrowserType.FIREFOX.value == "firefox"
    assert BrowserType.UNKNOWN.value == "unknown"


def test_artifact_type_enum():
    """Test ArtifactType enum values."""
    assert ArtifactType.HISTORY.value == "history"
    assert ArtifactType.COOKIE.value == "cookie"
    assert ArtifactType.WAL.value == "wal"


def test_artifact_creation():
    """Test creating an Artifact instance."""
    artifact = Artifact(
        artifact_type=ArtifactType.HISTORY,
        browser=BrowserType.CHROME,
        url="https://example.com",
        title="Example",
    )
    assert artifact.url == "https://example.com"
    assert artifact.browser == BrowserType.CHROME


def test_artifact_to_dict():
    """Test Artifact to_dict method."""
    artifact = Artifact(
        artifact_type=ArtifactType.HISTORY,
        browser=BrowserType.CHROME,
        url="https://example.com",
        title="Example",
    )
    d = artifact.to_dict()
    assert d["url"] == "https://example.com"
    assert d["browser"] == "chrome"


def test_detect_os():
    """Test OS detection returns a valid value."""
    os_type = detect_os()
    assert os_type in ("linux", "darwin", "windows")


def test_scan_result():
    """Test ScanResult properties."""
    result = ScanResult()
    assert result.total_artifacts == 0
    
    artifact = Artifact(
        artifact_type=ArtifactType.HISTORY,
        browser=BrowserType.CHROME,
        url="https://example.com",
    )
    result.artifacts.append(artifact)
    assert result.total_artifacts == 1


def test_browser_profile():
    """Test BrowserProfile creation."""
    profile = BrowserProfile(
        browser=BrowserType.CHROME,
        profile_path=Path("/tmp/test"),
        name="Default",
    )
    assert profile.browser == BrowserType.CHROME
    assert profile.name == "Default"
