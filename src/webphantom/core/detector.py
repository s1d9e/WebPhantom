"""Browser profile detection and discovery.

Scans filesystem to locate browser profiles across different operating systems.
"""

from __future__ import annotations

import os
from pathlib import Path

from webphantom.core.models import BrowserProfile, BrowserType

# Browser profile paths by OS
BROWSER_PATHS: dict[str, dict[BrowserType, list[str]]] = {
    "linux": {
        BrowserType.CHROME: [
            "~/.config/google-chrome",
            "~/.config/chromium",
            "~/.config/google-chrome-beta",
            "~/.config/google-chrome-dev",
        ],
        BrowserType.FIREFOX: [
            "~/.mozilla/firefox",
        ],
        BrowserType.BRAVE: [
            "~/.config/BraveSoftware/Brave-Browser",
        ],
        BrowserType.EDGE: [
            "~/.config/microsoft-edge",
        ],
    },
    "darwin": {
        BrowserType.CHROME: [
            "~/Library/Application Support/Google/Chrome",
        ],
        BrowserType.FIREFOX: [
            "~/Library/Application Support/Firefox/Profiles",
        ],
        BrowserType.SAFARI: [
            "~/Library/Safari",
        ],
        BrowserType.BRAVE: [
            "~/Library/Application Support/BraveSoftware/Brave-Browser",
        ],
        BrowserType.EDGE: [
            "~/Library/Application Support/Microsoft Edge",
        ],
    },
    "windows": {
        BrowserType.CHROME: [
            "~\\AppData\\Local\\Google\\Chrome\\User Data",
        ],
        BrowserType.FIREFOX: [
            "~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles",
        ],
        BrowserType.BRAVE: [
            "~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data",
        ],
        BrowserType.EDGE: [
            "~\\AppData\\Local\\Microsoft\\Edge\\User Data",
        ],
    },
}


def detect_os() -> str:
    """Detect the current operating system."""
    if os.name == "nt":
        return "windows"
    elif os.name == "posix":
        import platform
        if platform.system() == "Darwin":
            return "darwin"
        return "linux"
    return "linux"


def find_browser_profiles(root_path: Path | None = None) -> list[BrowserProfile]:
    """Find all browser profiles on the system.

    Args:
        root_path: Optional root path to scan instead of default OS paths.

    Returns:
        List of detected browser profiles.
    """
    profiles: list[BrowserProfile] = []
    os_type = detect_os()

    if root_path:
        profiles.extend(_scan_custom_path(root_path))
        return profiles

    browser_paths = BROWSER_PATHS.get(os_type, {})

    for browser_type, paths in browser_paths.items():
        for path_str in paths:
            base_path = Path(path_str).expanduser()
            if base_path.exists():
                found = _scan_browser_dir(base_path, browser_type, os_type)
                profiles.extend(found)

    return profiles


def _scan_browser_dir(
    base_path: Path, browser_type: BrowserType, os_type: str
) -> list[BrowserProfile]:
    """Scan a browser directory for profiles."""
    profiles: list[BrowserProfile] = []

    if browser_type == BrowserType.FIREFOX:
        for item in base_path.iterdir():
            if item.is_dir() and (item / "places.sqlite").exists():
                profiles.append(BrowserProfile(
                    browser=browser_type,
                    profile_path=item,
                    name=item.name,
                    os_type=os_type,
                ))
    else:
        default_profile = base_path / "Default"
        if default_profile.exists():
            profiles.append(BrowserProfile(
                browser=browser_type,
                profile_path=default_profile,
                name="Default",
                os_type=os_type,
            ))

        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("Profile"):
                has_db = (item / "History").exists() or (item / "places.sqlite").exists()
                if has_db:
                    profiles.append(BrowserProfile(
                        browser=browser_type,
                        profile_path=item,
                        name=item.name,
                        os_type=os_type,
                    ))

    return profiles


def _scan_custom_path(root_path: Path) -> list[BrowserProfile]:
    """Scan a custom path for browser artifacts."""
    profiles: list[BrowserProfile] = []

    for db_file in root_path.rglob("History"):
        profile_dir = db_file.parent
        profiles.append(BrowserProfile(
            browser=BrowserType.UNKNOWN,
            profile_path=profile_dir,
            name=profile_dir.name,
            os_type="unknown",
        ))

    for db_file in root_path.rglob("places.sqlite"):
        profile_dir = db_file.parent
        profiles.append(BrowserProfile(
            browser=BrowserType.FIREFOX,
            profile_path=profile_dir,
            name=profile_dir.name,
            os_type="unknown",
        ))

    return profiles
