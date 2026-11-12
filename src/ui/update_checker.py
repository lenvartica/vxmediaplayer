"""Asynchronous update discovery and verified Windows installer download."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from app_version import APP_VERSION

LOGGER = logging.getLogger(__name__)
API_URL = "https://api.github.com/repos/lenvartica/vxmediaplayer"
USER_AGENT = "VxPlayer-Updater"
MANIFEST_NAME = "VxPlayer-update.json"
INSTALLER_NAME = "VxPlayer-Setup.exe"


def _version_tuple(value: str) -> tuple[int, int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?", value)
    if not match:
        raise ValueError(f"Invalid VxPlayer version in update metadata: {value}")
    return tuple(int(part or 0) for part in match.groups())  # type: ignore[return-value]


def _get_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8-sig"))


def _asset_url(release: dict[str, Any], name: str) -> str:
    for asset in release.get("assets", []):
        if asset.get("name") == name:
            url = asset.get("browser_download_url")
            if isinstance(url, str) and url.startswith("https://"):
                return url
    raise ValueError(f"Release {release.get('tag_name')} is missing {name}.")


def find_update() -> dict[str, Any] | None:
    request = urllib.request.Request(
        f"{API_URL}/releases?per_page=30",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        releases = json.loads(response.read().decode("utf-8"))
    if not isinstance(releases, list):
        raise RuntimeError("GitHub returned an invalid release list.")

    installed = _version_tuple(APP_VERSION)
    candidates: list[dict[str, Any]] = []
    found_release = False
    found_valid_manifest = False
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        if tag != "continuous" and not re.fullmatch(
            r"v?\d+\.\d+\.\d+(?:\.\d+)?", str(tag)
        ):
            continue
        found_release = True
        try:
            manifest_url = _asset_url(release, MANIFEST_NAME)
            manifest = _get_json(manifest_url)
            version = str(manifest["version"])
            version_key = _version_tuple(version)
            installer = manifest.get("installer", INSTALLER_NAME)
            if installer != INSTALLER_NAME:
                raise ValueError("Update metadata names an unexpected installer.")
            if not re.fullmatch(r"[a-fA-F0-9]{64}", str(manifest.get("sha256", ""))):
                raise ValueError("Update metadata has an invalid installer checksum.")
            manifest_tag = str(manifest.get("tag", tag))
            if manifest_tag != tag:
                raise ValueError("Update metadata does not match its release tag.")
            installer_url = _asset_url(release, INSTALLER_NAME)
            found_valid_manifest = True
            if version_key <= installed:
                continue
            candidates.append(
                {
                    "version": version,
                    "version_key": version_key,
                    "installer_url": installer_url,
                    "sha256": str(manifest["sha256"]).lower(),
                    "release_url": release.get("html_url", ""),
                    "prerelease": bool(release.get("prerelease")),
                }
            )
        except (KeyError, TypeError, ValueError, urllib.error.URLError) as error:
            LOGGER.warning("Skipping unusable update release %s: %s", tag, error)
    if found_release and not found_valid_manifest:
        raise RuntimeError("No published VxPlayer release has valid update metadata.")
    if not candidates:
        return None
    newest = max(candidates, key=lambda item: item["version_key"])
    newest.pop("version_key")
    return newest


def download_update(update: dict[str, Any]) -> str:
    request = urllib.request.Request(
        update["installer_url"],
        headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
    )
    destination_dir = Path(tempfile.gettempdir()) / "VxPlayer-Updates"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / INSTALLER_NAME
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with destination.open("wb") as installer:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    installer.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest().lower() != update["sha256"].lower():
            raise RuntimeError("The downloaded installer failed its SHA-256 verification.")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return str(destination)


class UpdateWorker(QObject):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, operation: str, update: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._operation = operation
        self._update = update

    @pyqtSlot()
    def run(self) -> None:
        try:
            if self._operation == "check":
                result = find_update()
            elif self._operation == "download" and self._update is not None:
                result = download_update(self._update)
            else:
                raise ValueError(f"Unknown update operation: {self._operation}")
        except Exception as error:
            LOGGER.exception("VxPlayer update task failed")
            self.failed.emit(str(error))
        else:
            self.completed.emit(result)
