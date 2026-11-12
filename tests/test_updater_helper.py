from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import updater_helper


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


class UpdaterHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="VxPlayer-Update-")
        self.work_dir = Path(self.temporary.name)
        self.installation = tempfile.TemporaryDirectory(prefix="VxPlayer-Install-")
        self.install_root = Path(self.installation.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()
        self.installation.cleanup()

    def _plan(
        self,
        files: list[tuple[str, bytes]],
        installed_files: dict[str, str],
        deleted_files: list[str] | None = None,
    ) -> Path:
        downloaded = []
        for index, (relative, contents) in enumerate(files):
            source = self.work_dir / f"download-{index}"
            source.write_bytes(contents)
            downloaded.append(
                {"path": relative, "download": str(source), "sha256": digest(contents)}
            )
        plan = {
            "version": "1.1.0.0",
            "files": downloaded,
            "deleted_files": deleted_files or [],
            "install_state": {
                "version": "1.1.0.0",
                "files": installed_files,
            },
            "work_dir": str(self.work_dir),
        }
        path = self.work_dir / "update-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def test_apply_updates_only_changed_files_and_removes_obsolete_files(self) -> None:
        executable = self.install_root / "VxPlayer.exe"
        executable.write_bytes(b"old executable")
        obsolete = self.install_root / "vlc" / "old-plugin.dll"
        obsolete.parent.mkdir()
        obsolete.write_bytes(b"old plugin")
        user_file = self.install_root / "user-data.ini"
        user_file.write_text("keep", encoding="utf-8")

        executable_data = b"updated executable"
        module_data = b"new module"
        plan = self._plan(
            [("VxPlayer.exe", executable_data), ("_internal/new.pyc", module_data)],
            {
                "VxPlayer.exe": digest(executable_data),
                "_internal/new.pyc": digest(module_data),
            },
            ["vlc/old-plugin.dll"],
        )

        updater_helper.apply_plan(plan, self.install_root)

        self.assertEqual(executable.read_bytes(), executable_data)
        self.assertEqual(
            (self.install_root / "_internal" / "new.pyc").read_bytes(),
            module_data,
        )
        self.assertFalse(obsolete.exists())
        self.assertEqual(user_file.read_text(encoding="utf-8"), "keep")
        state = json.loads(
            (self.install_root / updater_helper.INSTALL_STATE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(state["version"], "1.1.0.0")
        self.assertFalse(plan.exists())

    def test_bad_hash_leaves_installed_files_unchanged(self) -> None:
        executable = self.install_root / "VxPlayer.exe"
        executable.write_bytes(b"old executable")
        plan = self._plan(
            [("VxPlayer.exe", b"untrusted bytes")],
            {"VxPlayer.exe": digest(b"expected bytes")},
        )

        with self.assertRaisesRegex(ValueError, "failed validation"):
            updater_helper.apply_plan(plan, self.install_root)

        self.assertEqual(executable.read_bytes(), b"old executable")
        self.assertFalse((self.install_root / updater_helper.INSTALL_STATE_NAME).exists())

    def test_failed_replace_rolls_back_every_prior_file(self) -> None:
        first = self.install_root / "VxPlayer.exe"
        second = self.install_root / "module.pyc"
        first.write_bytes(b"old app")
        second.write_bytes(b"old module")
        new_first = b"new app"
        new_second = b"new module"
        plan = self._plan(
            [("VxPlayer.exe", new_first), ("module.pyc", new_second)],
            {
                "VxPlayer.exe": digest(new_first),
                "module.pyc": digest(new_second),
            },
        )

        real_replace = updater_helper.os.replace
        failed_once = False

        def fail_second_install(source: str | Path, destination: str | Path) -> None:
            nonlocal failed_once
            if (
                Path(source).parent.name == "staged"
                and Path(source).name == "module.pyc"
                and not failed_once
            ):
                failed_once = True
                raise OSError("simulated disk failure")
            real_replace(source, destination)

        with patch.object(updater_helper.os, "replace", side_effect=fail_second_install):
            with self.assertRaisesRegex(OSError, "simulated disk failure"):
                updater_helper.apply_plan(plan, self.install_root)

        self.assertEqual(first.read_bytes(), b"old app")
        self.assertEqual(second.read_bytes(), b"old module")
        self.assertFalse((self.install_root / updater_helper.INSTALL_STATE_NAME).exists())

    def test_rejects_traversal_before_touching_install(self) -> None:
        plan = self._plan(
            [("../outside.txt", b"bad")],
            {"../outside.txt": digest(b"bad")},
        )

        with self.assertRaisesRegex(ValueError, "invalid installed file"):
            updater_helper.apply_plan(plan, self.install_root)

        self.assertEqual(list(self.install_root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
