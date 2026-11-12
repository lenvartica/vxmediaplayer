"""Application preferences dialog."""

from __future__ import annotations

import sys

from PyQt6.QtGui import QKeySequence, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QKeySequenceEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    SHORTCUTS = (
        ("play", "Play / pause", "Space"),
        ("open", "Open media", "Ctrl+O"),
        ("seek_back", "Skip back 10 seconds", "Left"),
        ("seek_forward", "Skip forward 10 seconds", "Right"),
        ("mute", "Mute / unmute", "M"),
        ("fullscreen", "Toggle fullscreen", "F"),
        ("exit_fullscreen", "Exit fullscreen", "Escape"),
        ("stop", "Stop playback", "S"),
        ("previous", "Previous queue item", "Ctrl+Left"),
        ("next", "Next queue item", "Ctrl+Right"),
    )

    def __init__(
        self,
        settings: object,
        audio_devices: list[tuple[str, str]],
        parent=None,
        tray_available: bool = True,
    ):
        super().__init__(parent)
        self.setWindowTitle("VxPlayer Settings")
        self.setMinimumWidth(420)
        self.settings = settings
        self.subtitle_delay = QSpinBox()
        self.subtitle_delay.setRange(-5000, 5000)
        self.subtitle_delay.setSuffix(" ms")
        self.subtitle_delay.setValue(int(settings.value("subtitle_delay", 0)))

        self.subtitle_size = QSpinBox()
        self.subtitle_size.setRange(12, 48)
        self.subtitle_size.setSuffix(" px")
        self.subtitle_size.setValue(int(settings.value("subtitle_size", 22)))

        self.subtitle_color = QLineEdit(str(settings.value("subtitle_color", "#FFFFFF")))
        self.subtitle_color.setMaxLength(7)
        self.subtitle_color.setPlaceholderText("#FFFFFF")
        self.subtitle_color.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"#[0-9A-Fa-f]{6}"))
        )

        self.subtitle_margin = QSpinBox()
        self.subtitle_margin.setRange(0, 200)
        self.subtitle_margin.setSuffix(" px")
        self.subtitle_margin.setValue(int(settings.value("subtitle_margin", 24)))

        self.audio_delay = QSpinBox()
        self.audio_delay.setRange(-5000, 5000)
        self.audio_delay.setSuffix(" ms")
        self.audio_delay.setValue(int(settings.value("audio_delay", 0)))

        self.audio_device = QComboBox()
        self.audio_device.addItem("System default", "")
        for name, identifier in audio_devices:
            self.audio_device.addItem(name, identifier)
        saved_device = settings.value("audio_device", "")
        index = self.audio_device.findData(saved_device)
        if index >= 0:
            self.audio_device.setCurrentIndex(index)

        self.global_hotkeys = QCheckBox("Enable global keyboard and hardware media keys")
        self.global_hotkeys.setChecked(
            settings.value("global_hotkeys", "false") in (True, "true", "1")
        )
        self.global_hotkeys.setEnabled(sys.platform == "win32")
        self.minimize_to_tray = QCheckBox("Hide to the system tray when minimized or closed")
        self.minimize_to_tray.setChecked(
            settings.value("minimize_to_tray", "false") in (True, "true", "1")
        )
        self.minimize_to_tray.setEnabled(
            sys.platform == "win32" and tray_available
        )
        self.keep_awake = QCheckBox("Keep the PC and display awake during playback")
        self.keep_awake.setChecked(
            settings.value("keep_awake", "false") in (True, "true", "1")
        )
        self.keep_awake.setEnabled(sys.platform == "win32")
        self.start_with_windows = QCheckBox("Start VxPlayer when I sign in")
        self.start_with_windows.setChecked(
            settings.value("start_with_windows", "false") in (True, "true", "1")
        )
        self.start_with_windows.setEnabled(sys.platform == "win32")

        playback_form = QFormLayout()
        playback_form.addRow("Default subtitle delay", self.subtitle_delay)
        playback_form.addRow("Audio synchronization delay", self.audio_delay)
        playback_form.addRow("Subtitle font size", self.subtitle_size)
        playback_form.addRow("Subtitle color (#RRGGBB)", self.subtitle_color)
        playback_form.addRow("Subtitle bottom margin", self.subtitle_margin)
        playback_form.addRow("Audio output", self.audio_device)

        desktop_form = QFormLayout()
        desktop_form.addRow("System tray", self.minimize_to_tray)
        desktop_form.addRow("", self.global_hotkeys)
        self.global_shortcut_editors: dict[str, QKeySequenceEdit] = {}
        for key, label, default in (
            ("play", "Global play / pause", "Ctrl+Alt+Space"),
            ("next", "Global next track", "Ctrl+Alt+Right"),
            ("previous", "Global previous track", "Ctrl+Alt+Left"),
        ):
            editor = QKeySequenceEdit(
                QKeySequence(settings.value(f"global_shortcut_{key}", default))
            )
            editor.setEnabled(
                self.global_hotkeys.isChecked() and sys.platform == "win32"
            )
            self.global_shortcut_editors[key] = editor
            desktop_form.addRow(label, editor)
        desktop_form.addRow("", self.start_with_windows)
        desktop_form.addRow("", self.keep_awake)
        self.global_hotkeys.toggled.connect(
            lambda enabled: [
                editor.setEnabled(enabled)
                for editor in self.global_shortcut_editors.values()
            ]
        )
        self.shortcut_editors: dict[str, QKeySequenceEdit] = {}
        shortcut_form = QFormLayout()
        for key, label, default in self.SHORTCUTS:
            editor = QKeySequenceEdit(
                QKeySequence(settings.value(f"shortcut_{key}", default))
            )
            self.shortcut_editors[key] = editor
            shortcut_form.addRow(f"{label} shortcut", editor)

        tabs = QTabWidget()
        playback_page = QWidget()
        playback_page.setLayout(playback_form)
        desktop_page = QWidget()
        desktop_page.setLayout(desktop_form)
        shortcut_page = QWidget()
        shortcut_page.setLayout(shortcut_form)
        tabs.addTab(playback_page, "Playback")
        tabs.addTab(desktop_page, "Windows")
        tabs.addTab(shortcut_page, "Shortcuts")
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def accept(self) -> None:
        if not self.subtitle_color.hasAcceptableInput():
            self.subtitle_color.setFocus()
            return
        self.settings.setValue("subtitle_delay", self.subtitle_delay.value())
        self.settings.setValue("audio_delay", self.audio_delay.value())
        self.settings.setValue("subtitle_size", self.subtitle_size.value())
        self.settings.setValue("subtitle_color", self.subtitle_color.text())
        self.settings.setValue("subtitle_margin", self.subtitle_margin.value())
        self.settings.setValue("audio_device", self.audio_device.currentData())
        self.settings.setValue("global_hotkeys", self.global_hotkeys.isChecked())
        self.settings.setValue("minimize_to_tray", self.minimize_to_tray.isChecked())
        self.settings.setValue("keep_awake", self.keep_awake.isChecked())
        self.settings.setValue("start_with_windows", self.start_with_windows.isChecked())
        for key, editor in self.global_shortcut_editors.items():
            self.settings.setValue(
                f"global_shortcut_{key}", editor.keySequence().toString()
            )
        for key, editor in self.shortcut_editors.items():
            self.settings.setValue(
                f"shortcut_{key}", editor.keySequence().toString()
            )
        super().accept()
