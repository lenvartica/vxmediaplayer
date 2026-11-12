"""Optional Windows desktop integrations used by VxPlayer."""

from __future__ import annotations

import ctypes
import logging
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter
from PyQt6.QtWidgets import QApplication

LOGGER = logging.getLogger(__name__)
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

SPECIAL_KEYS = {
    "SPACE": 0x20,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
}


def _parse_hotkey(sequence: str) -> tuple[int, int]:
    parts = [part.strip() for part in sequence.split("+")]
    if not parts or not parts[-1] or len(parts) > 4:
        raise ValueError(f"Unsupported global shortcut: {sequence}")
    modifiers = 0
    modifier_values = {
        "CTRL": MOD_CONTROL,
        "CONTROL": MOD_CONTROL,
        "ALT": MOD_ALT,
        "SHIFT": MOD_SHIFT,
        "WIN": MOD_WIN,
        "META": MOD_WIN,
    }
    for modifier in parts[:-1]:
        value = modifier_values.get(modifier.upper())
        if value is None or modifiers & value:
            raise ValueError(f"Unsupported global shortcut: {sequence}")
        modifiers |= value
    if modifiers == 0:
        raise ValueError("Global shortcuts must include Ctrl, Alt, Shift, or Windows.")

    key_name = parts[-1].upper()
    if len(key_name) == 1 and key_name.isascii() and key_name.isalnum():
        virtual_key = ord(key_name)
    elif key_name in SPECIAL_KEYS:
        virtual_key = SPECIAL_KEYS[key_name]
    elif key_name.startswith("F") and key_name[1:].isdigit():
        number = int(key_name[1:])
        if not 1 <= number <= 24:
            raise ValueError(f"Unsupported global shortcut: {sequence}")
        virtual_key = 0x70 + number - 1
    else:
        raise ValueError(f"Unsupported global shortcut key: {key_name}")
    return modifiers | MOD_NOREPEAT, virtual_key


class _HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, callbacks: dict[int, Callable[[], None]]) -> None:
        super().__init__()
        self._callbacks = callbacks

    def nativeEventFilter(self, event_type, message):
        if sys.platform != "win32":
            return False, 0
        try:
            event = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
        except (TypeError, ValueError, OSError):
            LOGGER.debug("Could not decode Windows native message", exc_info=True)
            return False, 0
        if event.message != WM_HOTKEY:
            return False, 0
        callback = self._callbacks.get(int(event.wParam))
        if callback is not None:
            callback()
            return True, 0
        return False, 0


class WindowsGlobalHotkeys:
    """Registers opt-in Windows media keys and user-configurable global shortcuts."""

    MEDIA_HOTKEYS = (
        (1, 0xB3, "hardware play/pause key"),
        (2, 0xB0, "hardware next-track key"),
        (3, 0xB1, "hardware previous-track key"),
    )
    CUSTOM_IDS = {"play": 11, "next": 12, "previous": 13}

    def __init__(self, application: QApplication) -> None:
        self._application = application
        self._user32 = None
        self._filter: _HotkeyEventFilter | None = None
        self._registered_ids: list[int] = []
        self._installed = False

    def unregister(self) -> None:
        if self._user32:
            for hotkey_id in self._registered_ids:
                self._user32.UnregisterHotKey(None, hotkey_id)
        self._registered_ids.clear()
        if self._installed and self._filter is not None:
            self._application.removeNativeEventFilter(self._filter)
        self._filter = None
        self._installed = False

    def register(
        self,
        callbacks: dict[str, Callable[[], None]],
        shortcuts: dict[str, str],
    ) -> list[str]:
        self.unregister()
        if sys.platform != "win32":
            raise RuntimeError("Global keyboard shortcuts are available on Windows only.")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.RegisterHotKey.argtypes = (
            wintypes.HWND,
            wintypes.INT,
            wintypes.UINT,
            wintypes.UINT,
        )
        self._user32.RegisterHotKey.restype = wintypes.BOOL
        self._user32.UnregisterHotKey.argtypes = (wintypes.HWND, wintypes.INT)
        self._user32.UnregisterHotKey.restype = wintypes.BOOL

        callback_map: dict[int, Callable[[], None]] = {}
        registrations: list[tuple[int, int, int, Callable[[], None], str]] = []
        for hotkey_id, virtual_key, description in self.MEDIA_HOTKEYS:
            action = "play" if hotkey_id == 1 else "next" if hotkey_id == 2 else "previous"
            registrations.append(
                (hotkey_id, MOD_NOREPEAT, virtual_key, callbacks[action], description)
            )
        for action, hotkey_id in self.CUSTOM_IDS.items():
            modifiers, virtual_key = _parse_hotkey(shortcuts[action])
            registrations.append(
                (hotkey_id, modifiers, virtual_key, callbacks[action], shortcuts[action])
            )

        conflicts: list[str] = []
        for hotkey_id, modifiers, virtual_key, callback, description in registrations[:3]:
            if not self._user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
                conflicts.append(description)
                continue
            self._registered_ids.append(hotkey_id)
            callback_map[hotkey_id] = callback

        for hotkey_id, modifiers, virtual_key, callback, description in registrations[3:]:
            if not self._user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
                error = ctypes.get_last_error()
                self.unregister()
                raise RuntimeError(
                    f"Could not register global shortcut '{description}' "
                    f"(Windows error {error}). It may already be in use."
                )
            self._registered_ids.append(hotkey_id)
            callback_map[hotkey_id] = callback

        self._filter = _HotkeyEventFilter(callback_map)
        self._application.installNativeEventFilter(self._filter)
        self._installed = True
        return conflicts


def set_keep_awake(enabled: bool) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Keep-awake control is available on Windows only.")
    continuous = 0x80000000
    required = 0x00000001
    display = 0x00000002
    flags = continuous | required | display if enabled else continuous
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.SetThreadExecutionState.argtypes = (wintypes.DWORD,)
    kernel32.SetThreadExecutionState.restype = wintypes.DWORD
    if not kernel32.SetThreadExecutionState(flags):
        raise ctypes.WinError(ctypes.get_last_error())


def set_startup_registration(enabled: bool) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Windows sign-in startup is available on Windows only.")
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    if getattr(sys, "frozen", False):
        command = subprocess.list2cmdline([sys.executable])
    else:
        command = subprocess.list2cmdline(
            [sys.executable, str(Path(sys.argv[0]).resolve())]
        )
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, "VxPlayer", 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, "VxPlayer")
            except FileNotFoundError:
                pass
