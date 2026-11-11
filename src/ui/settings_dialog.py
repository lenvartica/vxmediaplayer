"""Application preferences dialog."""

from __future__ import annotations

from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequenceEdit,
    QSpinBox,
    QVBoxLayout,
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

    def __init__(self, settings: object, audio_devices: list[tuple[str, str]], parent=None):
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

        self.audio_device = QComboBox()
        self.audio_device.addItem("System default", "")
        for name, identifier in audio_devices:
            self.audio_device.addItem(name, identifier)
        saved_device = settings.value("audio_device", "")
        index = self.audio_device.findData(saved_device)
        if index >= 0:
            self.audio_device.setCurrentIndex(index)

        form = QFormLayout()
        form.addRow("Default subtitle delay", self.subtitle_delay)
        form.addRow("Subtitle font size", self.subtitle_size)
        form.addRow("Audio output", self.audio_device)
        self.shortcut_editors: dict[str, QKeySequenceEdit] = {}
        for key, label, default in self.SHORTCUTS:
            editor = QKeySequenceEdit(
                QKeySequence(settings.value(f"shortcut_{key}", default))
            )
            self.shortcut_editors[key] = editor
            form.addRow(f"{label} shortcut", editor)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self.settings.setValue("subtitle_delay", self.subtitle_delay.value())
        self.settings.setValue("subtitle_size", self.subtitle_size.value())
        self.settings.setValue("audio_device", self.audio_device.currentData())
        for key, editor in self.shortcut_editors.items():
            self.settings.setValue(
                f"shortcut_{key}", editor.keySequence().toString()
            )
        super().accept()
