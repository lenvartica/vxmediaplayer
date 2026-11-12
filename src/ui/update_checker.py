"""Asynchronous update discovery and verified Windows installer download."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from app_version import APP_VERSION

LOGGER = logging.getLogger(__name__)
API_URL = "https://api.github.com/repos/lenvartica/vxmediaplayer"
USER_AGENT = "VxPlayer-Updater"
MANIFEST_NAME = "VxPlayer-update.json"
INSTALLER_NAME = "VxPlayer-Setup.exe"
INSTALL_STATE_NAME = "VxPlayer-install.json"
UPDATE_SHARD_COUNT = 16


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


def _safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    return (
        bool(value)
        and bool(path.parts)
        and path.as_posix() == value
        and "\\" not in value
        and not windows_path.drive
        and not windows_path.is_absolute()
        and not path.is_absolute()
        and all(part not in ("", ".", "..") and ":" not in part for part in path.parts)
    )


def _installation_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _read_install_state() -> dict[str, Any] | None:
    state_path = _installation_root() / INSTALL_STATE_NAME
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        LOGGER.warning("Ignoring invalid installed-file manifest: %s", error)
        return None
    if not isinstance(state, dict) or not isinstance(state.get("files"), dict):
        LOGGER.warning("Ignoring invalid installed-file manifest at %s", state_path)
        return None
    files: dict[str, str] = {}
    for path, digest in state["files"].items():
        if (
            not isinstance(path, str)
            or not _safe_relative_path(path)
            or path.casefold() == INSTALL_STATE_NAME.casefold()
            or not isinstance(digest, str)
            or not re.fullmatch(r"[a-fA-F0-9]{64}", digest)
        ):
            LOGGER.warning("Installed-file manifest contains an invalid entry: %r", path)
            return None
        files[path] = digest.lower()
    return {"version": str(state.get("version", "")), "files": files}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_files(
    manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]]:
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("Update metadata does not contain its installed files.")
    raw_shards = manifest.get("shards")
    if not isinstance(raw_shards, dict) or len(raw_shards) != UPDATE_SHARD_COUNT:
        raise ValueError("Update metadata does not contain its update archives.")
    shards: dict[str, dict[str, Any]] = {}
    for index in range(UPDATE_SHARD_COUNT):
        shard_id = f"{index:02d}"
        shard = raw_shards.get(shard_id)
        expected_asset = f"VxPlayer-update-{shard_id}.zip"
        if (
            not isinstance(shard, dict)
            or shard.get("asset") != expected_asset
            or not re.fullmatch(r"[a-fA-F0-9]{64}", str(shard.get("sha256", "")))
            or type(shard.get("size")) is not int
            or shard["size"] < 0
        ):
            raise ValueError(f"Update metadata has an invalid update archive: {shard_id}.")
        shards[shard_id] = {
            "asset": expected_asset,
            "sha256": str(shard["sha256"]).lower(),
            "size": shard["size"],
        }

    files: dict[str, dict[str, str]] = {}
    for path, entry in entries.items():
        if (
            not isinstance(path, str)
            or not _safe_relative_path(path)
            or path.casefold() == INSTALL_STATE_NAME.casefold()
            or not isinstance(entry, dict)
        ):
            raise ValueError(f"Update metadata contains an invalid file path: {path!r}")
        digest = str(entry.get("sha256", "")).lower()
        shard_id = entry.get("shard")
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError(f"Update metadata has an invalid checksum for {path}.")
        if not isinstance(shard_id, str) or shard_id not in shards:
            raise ValueError(f"Update metadata has an invalid archive reference for {path}.")
        files[path] = {"sha256": digest, "shard": shard_id}
    return files, shards


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
    installed_is_continuous = installed[3] > 0
    installed_state = _read_install_state()
    candidates: list[dict[str, Any]] = []
    found_valid_manifest = False
    stable_releases = []
    continuous_releases = []
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        if tag == "continuous":
            if installed_is_continuous:
                continuous_releases.append(release)
            continue
        if release.get("prerelease") or not re.fullmatch(
            r"v?\d+\.\d+\.\d+(?:\.\d+)?", str(tag)
        ):
            continue
        stable_releases.append(release)
    selected_releases = []
    if stable_releases:
        selected_releases.append(
            max(stable_releases, key=lambda release: _version_tuple(str(release["tag_name"])))
        )
    if continuous_releases:
        selected_releases.append(continuous_releases[0])

    for release in selected_releases:
        tag = release["tag_name"]
        is_prerelease = bool(release.get("prerelease"))
        try:
            manifest_url = _asset_url(release, MANIFEST_NAME)
            manifest = _get_json(manifest_url)
            version = str(manifest["version"])
            version_key = _version_tuple(version)
            if tag != "continuous" and version_key != _version_tuple(str(tag)):
                raise ValueError("Update metadata version does not match its release tag.")
            installer = manifest.get("installer", INSTALLER_NAME)
            if installer != INSTALLER_NAME:
                raise ValueError("Update metadata names an unexpected installer.")
            if not re.fullmatch(r"[a-fA-F0-9]{64}", str(manifest.get("sha256", ""))):
                raise ValueError("Update metadata has an invalid installer checksum.")
            manifest_tag = str(manifest.get("tag", tag))
            if manifest_tag != tag:
                raise ValueError("Update metadata does not match its release tag.")
            installer_url = _asset_url(release, INSTALLER_NAME)
            package_files, package_shards = _manifest_files(manifest)
            found_valid_manifest = True
            if version_key <= installed:
                continue
            candidate = {
                "version": version,
                "version_key": version_key,
                "installer_url": installer_url,
                "sha256": str(manifest["sha256"]).lower(),
                "release_url": release.get("html_url", ""),
                "prerelease": is_prerelease,
                "_release": release,
                "_files": package_files,
                "_shards": package_shards,
            }
            candidates.append(candidate)
        except (KeyError, OSError, TypeError, ValueError, urllib.error.URLError) as error:
            LOGGER.warning("Skipping unusable update release %s: %s", tag, error)
    if selected_releases and not found_valid_manifest:
        raise RuntimeError("No published VxPlayer release has valid update metadata.")
    if not candidates:
        return None
    newest = max(candidates, key=lambda item: item["version_key"])
    newest.pop("version_key")
    release = newest.pop("_release")
    package_files = newest.pop("_files")
    package_shards = newest.pop("_shards")
    if installed_state is None:
        newest["kind"] = "installer"
    else:
        current_files = installed_state["files"]
        changed_files = []
        install_root = _installation_root()
        for path, entry in package_files.items():
            if current_files.get(path) == entry["sha256"]:
                installed_file = install_root / Path(*PurePosixPath(path).parts)
                if installed_file.is_file() and _sha256_file(installed_file) == entry["sha256"]:
                    continue
            changed_files.append(
                {
                    "path": path,
                    "sha256": entry["sha256"],
                    "shard": entry["shard"],
                    "shard_url": _asset_url(
                        release, package_shards[entry["shard"]]["asset"]
                    ),
                    "shard_sha256": package_shards[entry["shard"]]["sha256"],
                }
            )
        newest["kind"] = "incremental"
        newest["files"] = changed_files
        newest["deleted_files"] = sorted(set(current_files) - set(package_files))
        newest["install_state"] = {
            "version": newest["version"],
            "files": {
                path: entry["sha256"] for path, entry in package_files.items()
            },
        }
    return newest


def download_update(update: dict[str, Any]) -> dict[str, str]:
    destination_dir = Path(tempfile.mkdtemp(prefix="VxPlayer-Update-"))

    def download_file(url: str, destination: Path, expected_hash: str) -> None:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
        )
        digest = hashlib.sha256()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                with destination.open("wb") as target:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        target.write(chunk)
                        digest.update(chunk)
            if digest.hexdigest().lower() != expected_hash.lower():
                raise RuntimeError(f"Downloaded update file failed SHA-256 verification: {destination.name}")
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    try:
        if update.get("kind") == "installer":
            destination = destination_dir / INSTALLER_NAME
            download_file(update["installer_url"], destination, update["sha256"])
            return {"kind": "installer", "path": str(destination)}
        if update.get("kind") != "incremental":
            raise ValueError("Update metadata has an unknown installation mode.")

        downloaded_files = []
        files_by_shard: dict[str, list[dict[str, Any]]] = {}
        for entry in update["files"]:
            relative = entry["path"]
            if not _safe_relative_path(relative):
                raise ValueError(f"Unsafe update path: {relative}")
            files_by_shard.setdefault(entry["shard"], []).append(entry)

        extracted_dir = destination_dir / "files"
        extracted_dir.mkdir()
        for shard_id, entries in files_by_shard.items():
            shard_path = destination_dir / f"shard-{shard_id}.zip"
            download_file(
                entries[0]["shard_url"],
                shard_path,
                entries[0]["shard_sha256"],
            )
            with zipfile.ZipFile(shard_path) as archive:
                members: dict[str, zipfile.ZipInfo] = {}
                for info in archive.infolist():
                    name = info.filename.rstrip("/")
                    if not name:
                        continue
                    if not _safe_relative_path(name) or name in members:
                        raise ValueError(f"Update archive contains an unsafe or duplicate path: {name}")
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise ValueError(f"Update archive contains a symbolic link: {name}")
                    members[name] = info
                for entry in entries:
                    relative = entry["path"]
                    info = members.get(relative)
                    if info is None or info.is_dir():
                        raise ValueError(f"Update archive is missing {relative}.")
                    digest = entry["sha256"].lower()
                    destination = extracted_dir / digest
                    with archive.open(info) as source, destination.open("wb") as target:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            target.write(chunk)
                    if _sha256_file(destination) != digest:
                        raise RuntimeError(f"Updated file failed SHA-256 verification: {relative}")
                    downloaded_files.append(
                        {"path": relative, "sha256": digest, "download": str(destination)}
                    )
        plan = {
            "version": update["version"],
            "files": downloaded_files,
            "deleted_files": update["deleted_files"],
            "install_state": update["install_state"],
            "work_dir": str(destination_dir),
        }
        plan_path = destination_dir / "update-plan.json"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        return {"kind": "incremental", "plan": str(plan_path)}
    except Exception:
        for item in destination_dir.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
        raise


class UpdateWorker(QObject):
    completed = pyqtSignal(str, object)
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
            self.completed.emit(self._operation, result)
