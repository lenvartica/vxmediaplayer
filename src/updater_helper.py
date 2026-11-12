"""Apply verified VxPlayer file updates after the player process has exited."""

from __future__ import annotations

import ctypes
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

INSTALL_STATE_NAME = "VxPlayer-install.json"
LOGGER = logging.getLogger("VxPlayerUpdater")


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
        and value.casefold() != INSTALL_STATE_NAME.casefold()
    )


def _target_path(root: Path, relative: str) -> Path:
    if not _safe_relative_path(relative):
        raise ValueError(f"Unsafe installed-file path: {relative!r}")
    target = root.joinpath(*PurePosixPath(relative).parts)
    if not target.resolve(strict=False).is_relative_to(root.resolve()):
        raise ValueError(f"Update path escapes the installation directory: {relative}")
    return target


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or not isinstance(state.get("files"), dict):
        raise ValueError("The update plan has no valid installed-file manifest.")
    files: dict[str, str] = {}
    seen: set[str] = set()
    for relative, digest in state["files"].items():
        if (
            not isinstance(relative, str)
            or not _safe_relative_path(relative)
            or relative.casefold() in seen
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in digest)
        ):
            raise ValueError(f"The update plan contains an invalid installed file: {relative!r}")
        seen.add(relative.casefold())
        files[relative] = digest.lower()
    version = state.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("The update plan has no target version.")
    return {"version": version, "files": files}


def apply_plan(plan_path: Path, install_root: Path) -> None:
    plan_path = plan_path.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(plan.get("files"), list):
        raise ValueError("The incremental update plan is invalid.")
    new_state = _validated_state(plan.get("install_state"))
    root = install_root.resolve()
    work_dir = plan_path.parent
    temp_root = Path(tempfile.gettempdir()).resolve()
    declared_work_dir = Path(plan.get("work_dir", "")).resolve()
    if (
        not work_dir.is_dir()
        or work_dir.is_symlink()
        or declared_work_dir != work_dir
        or not work_dir.is_relative_to(temp_root)
        or not work_dir.name.startswith("VxPlayer-Update-")
        or work_dir.is_relative_to(root)
        or root.is_relative_to(work_dir)
    ):
        raise ValueError("The staged update files are missing.")

    updates: dict[str, tuple[Path, str]] = {}
    for entry in plan["files"]:
        if not isinstance(entry, dict):
            raise ValueError("The update plan contains an invalid file entry.")
        relative = entry.get("path")
        source = Path(entry.get("download", "")).resolve()
        digest = str(entry.get("sha256", "")).lower()
        if (
            not isinstance(relative, str)
            or not _safe_relative_path(relative)
            or relative not in new_state["files"]
            or new_state["files"][relative] != digest
            or relative.casefold() in {item.casefold() for item in updates}
            or not source.is_relative_to(work_dir)
            or not source.is_file()
            or _sha256_file(source) != digest
        ):
            raise ValueError(f"The staged update file failed validation: {relative!r}")
        updates[relative] = (source, digest)

    deleted = plan.get("deleted_files", [])
    if not isinstance(deleted, list):
        raise ValueError("The update plan contains an invalid removed-file list.")
    deleted_paths: list[str] = []
    seen_deleted: set[str] = set()
    new_casefolded = {relative.casefold(): relative for relative in new_state["files"]}
    for relative in deleted:
        if (
            not isinstance(relative, str)
            or not _safe_relative_path(relative)
            or relative in new_state["files"]
            or relative.casefold() in seen_deleted
        ):
            raise ValueError(f"The update plan contains an invalid removed file: {relative!r}")
        if relative.casefold() in new_casefolded and new_casefolded[relative.casefold()] != relative:
            raise ValueError(f"Case-only path changes are not supported: {relative}")
        seen_deleted.add(relative.casefold())
        deleted_paths.append(relative)

    for relative in new_state["files"]:
        _target_path(root, relative)
    for relative in deleted_paths:
        _target_path(root, relative)

    stage_root = root / f".vxplayer-update-{uuid.uuid4().hex}"
    staged_root = stage_root / "staged"
    backup_root = stage_root / "backup"
    staged_files: dict[str, Path] = {}
    operations: list[dict[str, Any]] = []
    stage_root.mkdir()
    preserve_stage = False
    try:
        for relative, (source, _) in updates.items():
            staged = staged_root.joinpath(*PurePosixPath(relative).parts)
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, staged)
            staged_files[relative] = staged

        changes = [(relative, staged_files[relative]) for relative in updates]
        changes.extend((relative, None) for relative in deleted_paths)
        for relative, staged in changes:
            target = _target_path(root, relative)
            backup = backup_root.joinpath(*PurePosixPath(relative).parts)
            operation = {
                "target": target,
                "backup": backup,
                "had_old": target.exists(),
                "installed": False,
            }
            operations.append(operation)
            if operation["had_old"]:
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)
            if staged is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged, target)
                operation["installed"] = True

        state_target = root / INSTALL_STATE_NAME
        state_backup = backup_root / INSTALL_STATE_NAME
        state_staged = stage_root / "install-state.json"
        state_staged.write_text(json.dumps(new_state, indent=2), encoding="utf-8")
        state_operation = {
            "target": state_target,
            "backup": state_backup,
            "had_old": state_target.exists(),
            "installed": False,
        }
        operations.append(state_operation)
        if state_operation["had_old"]:
            state_backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(state_target, state_backup)
        os.replace(state_staged, state_target)
        state_operation["installed"] = True
    except Exception as error:
        rollback_errors: list[str] = []
        for operation in reversed(operations):
            target = operation["target"]
            backup = operation["backup"]
            try:
                if operation["installed"] and target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                if operation["had_old"] and backup.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup, target)
            except OSError as rollback_error:
                rollback_errors.append(f"{target}: {rollback_error}")
        if rollback_errors:
            preserve_stage = True
            raise RuntimeError(
                f"Update failed: {error}. Rollback was incomplete; recovery files remain at "
                f"{stage_root}. " + "; ".join(rollback_errors)
            ) from error
        raise
    finally:
        if not preserve_stage:
            shutil.rmtree(stage_root, ignore_errors=True)
        shutil.rmtree(work_dir, ignore_errors=True)


def _is_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def _can_write(directory: Path) -> bool:
    try:
        descriptor, probe_name = tempfile.mkstemp(prefix=".vxplayer-update-test-", dir=directory)
        os.close(descriptor)
        Path(probe_name).unlink()
        return True
    except OSError:
        return False


def _launch_elevated(arguments: list[str]) -> bool:
    command_line = subprocess.list2cmdline(arguments)
    shell = ctypes.windll.shell32
    shell.ShellExecuteW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]
    shell.ShellExecuteW.restype = ctypes.c_void_p
    result = shell.ShellExecuteW(None, "runas", sys.executable, command_line, None, 1)
    return bool(result and int(result) > 32)


def _wait_for_parent(pid: int, timeout_ms: int = 120_000) -> None:
    if os.name != "nt":
        return
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.OpenProcess(0x00100000, False, pid)
    if not handle:
        return
    try:
        result = kernel.WaitForSingleObject(handle, timeout_ms)
        if result == 0x00000102:
            raise TimeoutError("VxPlayer did not close in time to apply the update.")
        if result == 0xFFFFFFFF:
            raise OSError("Windows could not wait for VxPlayer to close.")
    finally:
        kernel.CloseHandle(handle)


def _restart_player(install_root: Path, media_path: str | None) -> None:
    executable = install_root / "VxPlayer.exe"
    if executable.is_file():
        arguments = [str(executable)]
        if media_path and Path(media_path).is_file():
            arguments.append(media_path)
        subprocess.Popen(arguments, cwd=str(install_root), close_fds=True)


def _cleanup_work_directory(plan_path: Path, install_root: Path) -> None:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        work_dir = Path(plan["work_dir"]).resolve()
        plan_parent = plan_path.resolve().parent
        temp_root = Path(tempfile.gettempdir()).resolve()
        root = install_root.resolve()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return
    if (
        work_dir == plan_parent
        and work_dir.is_dir()
        and not work_dir.is_symlink()
        and work_dir.is_relative_to(temp_root)
        and work_dir.name.startswith("VxPlayer-Update-")
        and not work_dir.is_relative_to(root)
        and not root.is_relative_to(work_dir)
    ):
        shutil.rmtree(work_dir, ignore_errors=True)


def _show_error(message: str) -> None:
    LOGGER.error(message)
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, "VxPlayer update", 0x10)


def apply_and_restart(plan_path: Path, parent_pid: int, install_root: Path, media_path: str | None) -> int:
    if os.name == "nt" and not _is_admin() and not _can_write(install_root):
        if _launch_elevated(sys.argv[1:]):
            return 0
        _cleanup_work_directory(plan_path, install_root)
        _show_error("Administrator permission was not granted. The update was not installed.")
        _restart_player(install_root, media_path)
        return 1

    try:
        _wait_for_parent(parent_pid)
        apply_plan(plan_path, install_root)
    except Exception as error:
        _cleanup_work_directory(plan_path, install_root)
        _show_error(f"VxPlayer could not finish the update:\n\n{error}")
        _restart_player(install_root, media_path)
        return 1

    try:
        _restart_player(install_root, media_path)
    except OSError as error:
        _show_error(f"VxPlayer was updated, but could not be restarted:\n\n{error}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        filename=Path(tempfile.gettempdir()) / "VxPlayer-updater.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) not in (4, 5) or arguments[0] != "--apply":
        LOGGER.error("Invalid updater command line.")
        return 2
    _, plan, pid, install_root, *media = arguments
    try:
        return apply_and_restart(
            Path(plan),
            int(pid),
            Path(install_root),
            media[0] if media else None,
        )
    except Exception as error:
        _show_error(f"VxPlayer could not start the update:\n\n{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
