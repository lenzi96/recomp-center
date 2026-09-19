"""GitHub API client for checking releases and downloading assets."""

import os
import re
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any, Tuple
from .models import ReleaseInfo, GameProject

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.expanduser("~/.cache/recomp-center")
os.makedirs(CACHE_DIR, exist_ok=True)


class GitHubClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("GITHUB_TOKEN", "")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "Recomp-Center/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"
        return headers

    def get_latest_release(self, project: GameProject) -> Optional[ReleaseInfo]:
        """Fetch latest release info from GitHub API or cache."""
        if not project.repo:
            return None

        cache_file = os.path.join(CACHE_DIR, f"{project.id}_release.json")
        url = f"https://api.github.com/repos/{project.repo}/releases/latest"

        # Try API request
        data = None
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    # Cache successful response
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                    except Exception as e:
                        logger.warning(f"Failed to cache release for {project.id}: {e}")
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP error fetching release for {project.repo}: {e.code} {e.reason}")
            # Fall back to cache if rate-limited
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Network error fetching release for {project.repo}: {e}")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass

        if not data:
            return None

        # Identify best Linux asset
        tag_name = data.get("tag_name", "")
        name = data.get("name", "") or tag_name
        published_at = data.get("published_at", "")
        body = data.get("body", "")
        html_url = data.get("html_url", "")

        assets = data.get("assets", [])
        best_asset = self._select_linux_asset(assets, project.linux_asset_patterns)

        if not best_asset:
            return None

        return ReleaseInfo(
            tag_name=tag_name,
            name=name,
            published_at=published_at,
            body=body,
            html_url=html_url,
            download_url=best_asset.get("browser_download_url", ""),
            asset_name=best_asset.get("name", ""),
            asset_size=best_asset.get("size", 0)
        )

    def _select_linux_asset(self, assets: List[Dict[str, Any]], patterns: List[str]) -> Optional[Dict[str, Any]]:
        """Select best matching asset for Linux (AppImage, x86_64, tar.gz, etc.)."""
        if not assets:
            return None

        # Exclude Windows/Mac/Switch/iOS/Android assets explicitly
        exclude_keywords = [
            ".exe", ".msi", "windows", "win32", "win64", "win-x64", "win.zip",
            ".dmg", "macos", "osx", "darwin",
            ".nsp", ".nro", "switch", "wiiu", "3ds", "vita",
            ".apk", ".ipa", "android", "ios",
            ".deb", ".rpm"  # Prefer standalone AppImage / portable tarball for portable manager
        ]

        # Filter out mismatching CPU architectures
        import platform
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            exclude_keywords.extend(["arm64", "aarch64", "armv7", "armhf"])
        elif machine in ("aarch64", "arm64"):
            exclude_keywords.extend(["x86_64", "amd64", "x86", "i686", "i386"])

        candidates = []
        for a in assets:
            fname = a.get("name", "").lower()
            if any(ex in fname for ex in exclude_keywords):
                continue
            candidates.append(a)

        if not candidates:
            # Fall back to all assets excluding .exe and .dmg
            candidates = [a for a in assets if not a.get("name", "").lower().endswith((".exe", ".dmg", ".msi"))]

        # Prioritize AppImages
        for a in candidates:
            if a.get("name", "").lower().endswith(".appimage"):
                return a

        # Prioritize Linux tar.gz / tar.xz / zip with linux or x86_64 in name
        for a in candidates:
            fname = a.get("name", "").lower()
            if "linux" in fname and any(fname.endswith(ext) for ext in [".tar.gz", ".tgz", ".tar.xz", ".zip", ""]):
                return a

        # Check for any candidate matching custom patterns
        for pattern in patterns:
            pat_lower = pattern.lower()
            for a in candidates:
                if pat_lower in a.get("name", "").lower():
                    return a

        # Default to first non-windows candidate
        if candidates:
            return candidates[0]

        return None
