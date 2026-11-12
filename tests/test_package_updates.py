from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import package_updates


class PackageUpdateTests(unittest.TestCase):
    def test_prepare_creates_complete_state_and_balanced_update_archives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            output = root / "release"
            (bundle / "_internal" / "ui").mkdir(parents=True)
            (bundle / "vlc").mkdir()
            package_data = {
                "VxPlayer.exe": b"app executable",
                "_internal/ui/main_window.pyc": b"python module",
                "vlc/libvlc.dll": b"vlc runtime",
            }
            for relative, contents in package_data.items():
                (bundle / relative).write_bytes(contents)

            package_updates.prepare(bundle, output, "1.1.0.0")

            state = json.loads((bundle / "VxPlayer-install.json").read_text(encoding="utf-8"))
            index = json.loads((output / "VxPlayer-package-index.json").read_text(encoding="utf-8"))
            self.assertEqual(state["version"], "1.1.0.0")
            self.assertEqual(index["version"], "1.1.0.0")
            self.assertEqual(set(state["files"]), set(package_data))
            for relative, contents in package_data.items():
                entry = index["files"][relative]
                self.assertEqual(entry["sha256"], hashlib.sha256(contents).hexdigest())
                shard = output / f"VxPlayer-update-{entry['shard']}.zip"
                with zipfile.ZipFile(shard) as archive:
                    self.assertEqual(archive.read(relative), contents)
            self.assertEqual(len(index["shards"]), package_updates.SHARD_COUNT)

            manifest_path = output / "VxPlayer-update.json"
            package_updates.write_manifest(
                output / "VxPlayer-package-index.json",
                manifest_path,
                "1.1.0.0",
                "v1.1.0",
                "a" * 64,
                "commit",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["tag"], "v1.1.0")
            self.assertEqual(set(manifest["files"]), set(package_data))


if __name__ == "__main__":
    unittest.main()
