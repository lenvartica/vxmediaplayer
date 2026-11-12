from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
except ImportError:
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QObject = type("QObject", (), {})
    qtcore.pyqtSignal = lambda *args: object()
    qtcore.pyqtSlot = lambda *args: (lambda function: function)
    pyqt = types.ModuleType("PyQt6")
    pyqt.__path__ = []
    sys.modules["PyQt6"] = pyqt
    sys.modules["PyQt6.QtCore"] = qtcore

import ui.update_checker as update_checker
import updater_helper


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


class _Response:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            data, self.data = self.data, b""
            return data
        data, self.data = self.data[:size], self.data[size:]
        return data


class UpdateCheckerTests(unittest.TestCase):
    def test_stable_channel_chooses_stable_and_only_marks_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed_exe = b"old exe"
            unchanged_module = b"unchanged module"
            (root / "VxPlayer.exe").write_bytes(installed_exe)
            (root / "same.pyc").write_bytes(unchanged_module)
            files = {
                "VxPlayer.exe": {"sha256": digest(b"new exe"), "shard": "00"},
                "same.pyc": {"sha256": digest(unchanged_module), "shard": "01"},
            }
            shards = {
                f"{index:02d}": {
                    "asset": f"VxPlayer-update-{index:02d}.zip",
                    "sha256": f"{index:064x}",
                    "size": 20,
                }
                for index in range(update_checker.UPDATE_SHARD_COUNT)
            }
            manifest = {
                "version": "1.1.0.0",
                "tag": "v1.1.0",
                "installer": update_checker.INSTALLER_NAME,
                "sha256": "a" * 64,
                "files": files,
                "shards": shards,
            }
            assets = [
                {
                    "name": update_checker.MANIFEST_NAME,
                    "browser_download_url": "https://fixture/VxPlayer-update.json",
                },
                {
                    "name": update_checker.INSTALLER_NAME,
                    "browser_download_url": "https://fixture/VxPlayer-Setup.exe",
                },
                *[
                    {
                        "name": shard["asset"],
                        "browser_download_url": f"https://fixture/{shard['asset']}",
                    }
                    for shard in shards.values()
                ],
            ]
            stable_release = {
                "tag_name": "v1.1.0",
                "draft": False,
                "prerelease": False,
                "html_url": "https://fixture/releases/v1.1.0",
                "assets": assets,
            }
            continuous_release = {
                "tag_name": "continuous",
                "draft": False,
                "prerelease": True,
                "assets": [],
            }

            with (
                patch.object(update_checker, "APP_VERSION", "1.0.4.0"),
                patch.object(update_checker, "_installation_root", return_value=root),
                patch.object(
                    update_checker,
                    "_read_install_state",
                    return_value={
                        "version": "1.0.4.0",
                        "files": {
                            "VxPlayer.exe": digest(installed_exe),
                            "same.pyc": digest(unchanged_module),
                        },
                    },
                ),
                patch.object(
                    update_checker.urllib.request,
                    "urlopen",
                    return_value=_Response(json.dumps([continuous_release, stable_release]).encode()),
                ),
                patch.object(update_checker, "_get_json", return_value=manifest),
            ):
                update = update_checker.find_update()

            self.assertIsNotNone(update)
            self.assertEqual(update["version"], "1.1.0.0")
            self.assertEqual(update["kind"], "incremental")
            self.assertEqual([entry["path"] for entry in update["files"]], ["VxPlayer.exe"])

    def test_downloaded_shard_is_verified_and_only_requested_file_is_applied(self) -> None:
        updated = b"new executable"
        untouched = b"keep me"
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("VxPlayer.exe", updated)
            archive.writestr("data/unchanged.dat", untouched)
        shard_bytes = archive_buffer.getvalue()
        update = {
            "kind": "incremental",
            "version": "1.1.0.0",
            "files": [
                {
                    "path": "VxPlayer.exe",
                    "sha256": digest(updated),
                    "shard": "00",
                    "shard_url": "https://fixture/VxPlayer-update-00.zip",
                    "shard_sha256": digest(shard_bytes),
                }
            ],
            "deleted_files": [],
            "install_state": {
                "version": "1.1.0.0",
                "files": {
                    "VxPlayer.exe": digest(updated),
                    "data/unchanged.dat": digest(untouched),
                },
            },
        }
        with tempfile.TemporaryDirectory(prefix="VxPlayer-Install-") as temporary:
            install_root = Path(temporary)
            executable = install_root / "VxPlayer.exe"
            executable.write_bytes(b"old executable")
            (install_root / "data").mkdir()
            (install_root / "data" / "unchanged.dat").write_bytes(untouched)
            with patch.object(
                update_checker.urllib.request,
                "urlopen",
                return_value=_Response(shard_bytes),
            ):
                result = update_checker.download_update(update)

            self.assertEqual(result["kind"], "incremental")
            updater_helper.apply_plan(Path(result["plan"]), install_root)
            self.assertEqual(executable.read_bytes(), updated)
            self.assertEqual((install_root / "data" / "unchanged.dat").read_bytes(), untouched)


if __name__ == "__main__":
    unittest.main()
