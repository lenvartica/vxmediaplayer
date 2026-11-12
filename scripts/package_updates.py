"""Create a complete Windows payload plus hash-partitioned update archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

INSTALL_STATE_NAME = "VxPlayer-install.json"
SHARD_COUNT = 16


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(bundle_dir: Path, output_dir: Path, version: str) -> None:
    bundle_dir = bundle_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_files: dict[str, dict[str, str]] = {}
    shard_paths: dict[str, list[tuple[str, Path]]] = {
        f"{index:02d}": [] for index in range(SHARD_COUNT)
    }

    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file() or path.name.casefold() == INSTALL_STATE_NAME.casefold():
            continue
        relative = path.relative_to(bundle_dir).as_posix()
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError(f"Unsafe application package path: {relative}")
        shard_index = int(hashlib.sha256(relative.casefold().encode("utf-8")).hexdigest()[:8], 16)
        shard = f"{shard_index % SHARD_COUNT:02d}"
        package_files[relative] = {
            "sha256": _sha256_file(path),
            "shard": shard,
        }
        shard_paths[shard].append((relative, path))

    if not package_files:
        raise ValueError(f"The Windows application bundle is empty: {bundle_dir}")

    for shard, paths in shard_paths.items():
        archive_path = output_dir / f"VxPlayer-update-{shard}.zip"
        with zipfile.ZipFile(
            archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            for relative, source in paths:
                archive.write(source, arcname=relative)

    state = {"version": version, "files": {path: entry["sha256"] for path, entry in package_files.items()}}
    (bundle_dir / INSTALL_STATE_NAME).write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    index: dict[str, Any] = {
        "version": version,
        "files": package_files,
        "shards": {},
    }
    for shard in shard_paths:
        archive_path = output_dir / f"VxPlayer-update-{shard}.zip"
        index["shards"][shard] = {
            "asset": archive_path.name,
            "sha256": _sha256_file(archive_path),
            "size": archive_path.stat().st_size,
        }
    (output_dir / "VxPlayer-package-index.json").write_text(
        json.dumps(index, indent=2),
        encoding="utf-8",
    )


def write_manifest(
    index_path: Path,
    output_path: Path,
    version: str,
    tag: str,
    installer_sha256: str,
    commit: str,
) -> None:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("version") != version:
        raise ValueError("The package index version does not match the release version.")
    if len(installer_sha256) != 64 or any(
        character not in "0123456789abcdefABCDEF" for character in installer_sha256
    ):
        raise ValueError("The installer checksum is invalid.")
    manifest = {
        "version": version,
        "tag": tag,
        "installer": "VxPlayer-Setup.exe",
        "sha256": installer_sha256.lower(),
        "commit": commit,
        "files": index["files"],
        "shards": index["shards"],
    }
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--bundle-dir", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--version", required=True)
    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--index", type=Path, required=True)
    manifest_parser.add_argument("--output", type=Path, required=True)
    manifest_parser.add_argument("--version", required=True)
    manifest_parser.add_argument("--tag", required=True)
    manifest_parser.add_argument("--installer-sha256", required=True)
    manifest_parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    if args.command == "prepare":
        prepare(args.bundle_dir, args.output_dir, args.version)
    else:
        write_manifest(
            args.index,
            args.output,
            args.version,
            args.tag,
            args.installer_sha256,
            args.commit,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
