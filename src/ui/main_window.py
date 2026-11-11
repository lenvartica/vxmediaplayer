"""Main VxPlayer window and playback controls."""

from __future__ import annotations

import json
import logging
import time
from functools import lru_cache
from pathlib import Path

import vlc
from PyQt6.QtCore import QPoint, QSize, Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QMouseEvent, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from engine.equalizer import PRESETS
from engine.player import Player, SUPPORTED_MEDIA, SUBTITLE_SUFFIXES
from ui.playlist_widget import PlaylistWidget
from ui.settings_dialog import SettingsDialog

LOGGER = logging.getLogger(__name__)
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
MEDIA_FILTER = "Media files (" + " ".join(f"*{suffix}" for suffix in sorted(SUPPORTED_MEDIA)) + ")"
EQUALIZER_BANDS = ("60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k")


@lru_cache(maxsize=None)
def _icon(name: str) -> QIcon:
    return QIcon(_svg_pixmap(ASSET_DIR / "icons" / f"{name}.svg", 48))


def _svg_pixmap(path: Path, size: int) -> QPixmap:
    renderer = QSvgRenderer(str(path))
    if not renderer.isValid():
        raise FileNotFoundError(f"Could not load VxPlayer artwork: {path}")
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class VideoSurface(QWidget):
    interaction = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._press_position: QPoint | None = None
        self.setObjectName("videoSurface")
        self.setMinimumSize(480, 300)
        self.setToolTip("Click the center to play or pause; click either edge to skip 10 seconds.")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._press_position is not None
            and (event.position().toPoint() - self._press_position).manhattanLength()
            <= QApplication.startDragDistance()
        ):
            x = event.position().x()
            edge = self.width() * 0.18
            if x < edge:
                self.interaction.emit("backward")
            elif x >= self.width() - edge:
                self.interaction.emit("forward")
            else:
                self.interaction.emit("toggle")
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        self._press_position = None


def _read_string_list_setting(settings: QSettings, key: str) -> list[str]:
    try:
        value = settings.value(key, "[]")
        entries = value if isinstance(value, list) else json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        LOGGER.warning("Ignoring invalid saved list setting: %s", key)
        return []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, str)]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("Decan Konnect", "VxPlayer")
        self.setWindowTitle("VxPlayer")
        self.setWindowIcon(QIcon(_svg_pixmap(ASSET_DIR / "vxplayer.svg", 128)))
        self.resize(1280, 800)
        self.setMinimumSize(820, 540)
        self.setAcceptDrops(True)
        self._last_unmuted_volume = 100
        self._pip = False
        self._normal_geometry = None
        self._last_position_update = 0.0
        self._last_player_state = ""
        self._build_ui()
        try:
            self.player = Player(self.video_surface, self)
        except Exception as error:
            QMessageBox.critical(
                self,
                "LibVLC unavailable",
                f"VxPlayer could not initialize LibVLC.\n\n{error}\n\n"
                "Install VLC Media Player or provide the bundled LibVLC runtime.",
            )
            raise
        self._connect_player()
        self.player.set_subtitle_size(int(self.settings.value("subtitle_size", 22)))
        self.equalizer_dialog = EqualizerDialog(self.player.equalizer, self)
        self._restore_state()
        self._create_actions()
        self._create_menus()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 14, 18, 16)
        header = QHBoxLayout()
        brand_icon = QLabel()
        brand_icon.setObjectName("brandIcon")
        brand_icon.setAccessibleName("VxPlayer logo")
        brand_icon.setPixmap(
            _svg_pixmap(ASSET_DIR / "vxplayer.svg", 64).scaled(
                34,
                34,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        brand = QLabel("VXPLAYER")
        brand.setObjectName("brand")
        self.track_label = QLabel("Ready when you are")
        self.track_label.setObjectName("trackLabel")
        header.addWidget(brand_icon)
        header.addWidget(brand)
        header.addSpacing(20)
        header.addWidget(self.track_label, 1)
        self.open_button = QPushButton("Open media")
        self.open_button.setObjectName("primaryButton")
        self.subtitle_button = QPushButton("Subtitles")
        header.addWidget(self.subtitle_button)
        header.addWidget(self.open_button)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.video_surface = VideoSurface()
        self.playlist = PlaylistWidget()
        self.playlist.setMinimumWidth(250)
        splitter.addWidget(self.video_surface)
        splitter.addWidget(self.playlist)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([900, 300])
        outer.addWidget(splitter, 1)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_label = QLabel("00:00 / 00:00")
        seek_row = QHBoxLayout()
        seek_row.addWidget(self.position_slider, 1)
        seek_row.addWidget(self.position_label)
        outer.addLayout(seek_row)

        controls = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.previous_button.setIcon(_icon("previous"))
        self.previous_button.setToolTip("Previous item (Ctrl+Left)")
        self.seek_back_button = QPushButton("-10")
        self.seek_back_button.setIcon(_icon("seek-backward"))
        self.seek_back_button.setToolTip("Back 10 seconds (Left)")
        self.play_button = QPushButton("Play")
        self.play_button.setIcon(_icon("play"))
        self.play_button.setToolTip("Play or pause (Space)")
        self.play_button.setObjectName("primaryButton")
        self.next_button = QPushButton("Next")
        self.next_button.setIcon(_icon("next"))
        self.next_button.setToolTip("Next item (Ctrl+Right)")
        self.seek_forward_button = QPushButton("+10")
        self.seek_forward_button.setIcon(_icon("seek-forward"))
        self.seek_forward_button.setToolTip("Forward 10 seconds (Right)")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(_icon("stop"))
        self.stop_button.setToolTip("Stop playback (S)")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x", "3.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.equalizer_combo = QComboBox()
        self.equalizer_combo.addItems(PRESETS)
        self.equalizer_button = QPushButton("EQ bands")
        self.volume_label = QLabel("100%")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 300)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.setToolTip(
            "0–300% output gain. Start low; high volume can damage hearing or distort audio."
        )
        self.mute_button = QPushButton()
        self.mute_button.setIcon(_icon("volume"))
        self.mute_button.setToolTip("Mute or restore volume (M)")
        self.mute_button.setAccessibleName("Mute")
        self.pip_button = QPushButton("PiP")
        for button in (
            self.previous_button,
            self.seek_back_button,
            self.seek_forward_button,
            self.next_button,
            self.stop_button,
            self.mute_button,
        ):
            button.setObjectName("transportButton")
            button.setIconSize(QSize(18, 18))
        self.play_button.setIconSize(QSize(20, 20))
        for widget in (
            self.previous_button,
            self.seek_back_button,
            self.play_button,
            self.seek_forward_button,
            self.next_button,
            self.stop_button,
            self.speed_combo,
            self.pip_button,
        ):
            controls.addWidget(widget)
        outer.addLayout(controls)
        audio_controls = QHBoxLayout()
        for widget in (
            self.equalizer_combo,
            self.equalizer_button,
            self.mute_button,
            self.volume_label,
            self.volume_slider,
        ):
            audio_controls.addWidget(widget)
        audio_controls.addStretch(1)
        outer.addLayout(audio_controls)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(
            "Click the video center to play or pause; click either edge to skip 10 seconds."
        )
        self.open_button.clicked.connect(self.open_files)
        self.subtitle_button.clicked.connect(self.open_subtitle)
        self.playlist.add_button.clicked.connect(self.open_files)
        self.playlist.remove_button.clicked.connect(self.remove_selected)
        self.playlist.clear_button.clicked.connect(self.playlist.list_widget.clear)
        self.playlist.play_requested.connect(self.play_path)
        self.playlist.files_dropped.connect(self._queue_dropped_paths)
        self.play_button.clicked.connect(self._toggle_play)
        self.seek_back_button.clicked.connect(lambda: self._skip(-10_000))
        self.seek_forward_button.clicked.connect(lambda: self._skip(10_000))
        self.stop_button.clicked.connect(self._stop)
        self.previous_button.clicked.connect(lambda: self._step_queue(-1))
        self.next_button.clicked.connect(lambda: self._step_queue(1))
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.speed_combo.currentTextChanged.connect(
            lambda text: self._set_rate(float(text.rstrip("x")))
        )
        self.equalizer_combo.currentTextChanged.connect(self._set_equalizer)
        self.equalizer_button.clicked.connect(self.equalizer_dialog_open)
        self.pip_button.clicked.connect(self._toggle_pip)
        self.mute_button.clicked.connect(self._toggle_mute)
        self.position_slider.sliderReleased.connect(self._seek)
        self.video_surface.interaction.connect(self._handle_surface_interaction)

    def _connect_player(self) -> None:
        self.player.position_changed.connect(self._update_position)
        self.player.state_changed.connect(self._update_state)
        self.player.media_changed.connect(self._media_changed)
        self.player.error_occurred.connect(self._show_error)
        delay = int(self.settings.value("subtitle_delay", 0))
        self.player.set_subtitle_delay(delay)
        self.player.set_video_output(str(self.settings.value("audio_device", "")))

    def _create_actions(self) -> None:
        self.open_action = QAction("Open media...", self)
        self.open_action.setShortcut(QKeySequence(self.settings.value("shortcut_open", "Ctrl+O")))
        self.open_action.triggered.connect(self.open_files)
        self.play_action = QAction("Play / pause", self)
        self.play_action.setShortcut(QKeySequence(self.settings.value("shortcut_play", "Space")))
        self.play_action.triggered.connect(self._toggle_play)
        self.seek_back_action = QAction("Back 10 seconds", self)
        self.seek_back_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_seek_back", "Left"))
        )
        self.seek_back_action.triggered.connect(lambda: self._skip(-10_000))
        self.seek_forward_action = QAction("Forward 10 seconds", self)
        self.seek_forward_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_seek_forward", "Right"))
        )
        self.seek_forward_action.triggered.connect(lambda: self._skip(10_000))
        self.mute_action = QAction("Mute / unmute", self)
        self.mute_action.setShortcut(QKeySequence(self.settings.value("shortcut_mute", "M")))
        self.mute_action.triggered.connect(self._toggle_mute)
        self.fullscreen_action = QAction("Toggle fullscreen", self)
        self.fullscreen_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_fullscreen", "F"))
        )
        self.fullscreen_action.triggered.connect(self._toggle_fullscreen)
        self.stop_action = QAction("Stop playback", self)
        self.stop_action.setShortcut(QKeySequence(self.settings.value("shortcut_stop", "S")))
        self.stop_action.triggered.connect(self._stop)
        self.previous_action = QAction("Previous queue item", self)
        self.previous_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_previous", "Ctrl+Left"))
        )
        self.previous_action.triggered.connect(lambda: self._step_queue(-1))
        self.next_action = QAction("Next queue item", self)
        self.next_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_next", "Ctrl+Right"))
        )
        self.next_action.triggered.connect(lambda: self._step_queue(1))
        self.exit_fullscreen_action = QAction("Exit fullscreen", self)
        self.exit_fullscreen_action.setShortcut(
            QKeySequence(self.settings.value("shortcut_exit_fullscreen", "Escape"))
        )
        self.exit_fullscreen_action.triggered.connect(self._exit_fullscreen)
        self.settings_action = QAction("Settings...", self)
        self.settings_action.triggered.connect(self.open_settings)
        self.save_playlist_action = QAction("Save playlist...", self)
        self.save_playlist_action.triggered.connect(self.save_playlist)
        self.load_playlist_action = QAction("Open playlist...", self)
        self.load_playlist_action.triggered.connect(self.load_playlist)
        self.recent_menu_action = QAction("Clear recent files", self)
        self.recent_menu_action.triggered.connect(self._clear_recent)
        self.shortcut_help_action = QAction("Keyboard shortcuts", self)
        self.shortcut_help_action.triggered.connect(self._show_shortcuts)
        for action in (
            self.open_action, self.play_action, self.seek_back_action,
            self.seek_forward_action, self.mute_action, self.fullscreen_action,
            self.stop_action, self.previous_action, self.next_action,
            self.exit_fullscreen_action,
        ):
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            self.addAction(action)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        for action in (self.open_action, self.load_playlist_action, self.save_playlist_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        self.recent_menu = file_menu.addMenu("Recent files")
        self._refresh_recent_menu()
        self.menuBar().addAction(self.recent_menu_action)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self.shortcut_help_action)

    def open_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Open media", "", MEDIA_FILTER)
        if paths:
            self.playlist.add_paths(paths)
            self.play_path(paths[0])

    def play_path(self, path: str) -> None:
        try:
            self.player.open(path)
            self.playlist.select_path(str(Path(path).resolve()))
            self._add_recent(path)
        except (FileNotFoundError, RuntimeError, ValueError) as error:
            self._show_error(str(error))

    def open_subtitle(self) -> None:
        filters = "Subtitle files (" + " ".join(f"*{s}" for s in sorted(SUBTITLE_SUFFIXES)) + ")"
        path, _ = QFileDialog.getOpenFileName(self, "Open subtitles", "", filters)
        if path:
            try:
                self.player.set_subtitle(path)
                self.statusBar().showMessage(f"Subtitle loaded: {Path(path).name}", 4000)
            except (RuntimeError, ValueError) as error:
                self._show_error(str(error))

    def _handle_dropped_paths(self, paths: list[str]) -> None:
        subtitles = [path for path in paths if Path(path).suffix.lower() in SUBTITLE_SUFFIXES]
        media = [path for path in paths if Path(path).suffix.lower() in SUPPORTED_MEDIA]
        if media:
            self.play_path(media[0])
        if subtitles and self.player.current_path:
            try:
                self.player.set_subtitle(subtitles[0])
            except (RuntimeError, ValueError) as error:
                self._show_error(str(error))

    def _queue_dropped_paths(self, paths: list[str]) -> None:
        subtitles = [path for path in paths if Path(path).suffix.lower() in SUBTITLE_SUFFIXES]
        if subtitles and self.player.current_path:
            try:
                self.player.set_subtitle(subtitles[0])
            except (RuntimeError, ValueError) as error:
                self._show_error(str(error))

    def _toggle_play(self) -> None:
        self.player.toggle_play_pause()

    def _stop(self) -> None:
        self.player.stop()

    def _skip(self, offset_ms: int) -> None:
        self.player.seek_by(offset_ms)
        direction = "forward" if offset_ms > 0 else "back"
        self.statusBar().showMessage(f"Skipped 10 seconds {direction}.", 1400)

    def _handle_surface_interaction(self, action: str) -> None:
        if action == "backward":
            self._skip(-10_000)
        elif action == "forward":
            self._skip(10_000)
        else:
            self._toggle_play()

    def _toggle_mute(self) -> None:
        if self.volume_slider.value() > 0:
            self._last_unmuted_volume = self.volume_slider.value()
            self.volume_slider.setValue(0)
        else:
            self.volume_slider.setValue(self._last_unmuted_volume or 100)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()

    def _show_shortcuts(self) -> None:
        def shortcut(action: QAction) -> str:
            return action.shortcut().toString() or "Not set"

        QMessageBox.information(
            self,
            "Keyboard shortcuts",
            f"{shortcut(self.play_action)}  Play / pause\n"
            f"{shortcut(self.seek_back_action)} / {shortcut(self.seek_forward_action)}"
            "  Skip 10 seconds\n"
            f"{shortcut(self.previous_action)} / {shortcut(self.next_action)}"
            "  Previous / next queue item\n"
            f"{shortcut(self.mute_action)}  Mute / restore volume\n"
            f"{shortcut(self.fullscreen_action)}  Toggle fullscreen · Esc  Exit fullscreen\n"
            f"{shortcut(self.stop_action)}  Stop playback\n"
            f"{shortcut(self.open_action)}  Open media",
        )

    def _set_volume(self, value: int) -> None:
        self.player.set_volume(value)
        self.volume_label.setText(f"{value}%")
        self.mute_button.setIcon(_icon("mute" if value == 0 else "volume"))
        self.mute_button.setAccessibleName("Unmute" if value == 0 else "Mute")
        if value > 0:
            self._last_unmuted_volume = value

    def _set_rate(self, rate: float) -> None:
        self.player.set_rate(rate)

    def _set_equalizer(self, name: str) -> None:
        try:
            self.player.equalizer.set_preset(name)
            self.player.equalizer.set_enabled(name != "Flat")
            self.settings.setValue("equalizer_preset", name)
            self.equalizer_dialog.refresh()
        except (RuntimeError, ValueError) as error:
            self._show_error(str(error))

    def equalizer_dialog_open(self) -> None:
        self.equalizer_dialog.refresh()
        self.equalizer_dialog.exec()

    def _update_position(self, position: int, length: int) -> None:
        if length > 0 and not self.position_slider.isSliderDown():
            self.position_slider.setValue(int(position * 1000 / length))
        now = time.monotonic()
        if now - self._last_position_update >= 0.8:
            self.position_label.setText(f"{self._format_time(position)} / {self._format_time(length)}")
            self._last_position_update = now

    def _update_state(self, state: str) -> None:
        playing = state == "playing"
        self.play_button.setText("Pause" if playing else "Play")
        self.play_button.setIcon(_icon("pause" if playing else "play"))
        self.play_button.setToolTip(
            "Pause playback (Space)" if playing else "Play or pause (Space)"
        )
        self.play_button.setAccessibleName("Pause" if playing else "Play")
        if (
            state == "ended"
            and self._last_player_state != "ended"
            and self.playlist.list_widget.count() > 1
        ):
            self._step_queue(1)
        self._last_player_state = state

    def _media_changed(self, path: str) -> None:
        self.track_label.setText(Path(path).name)
        self.setWindowTitle(f"{Path(path).name} — VxPlayer")
        self.player.set_subtitle_delay(int(self.settings.value("subtitle_delay", 0)))

    def _seek(self) -> None:
        # Position is obtained from the slider's normalized value and duration.
        length = self.player.duration_ms
        if length > 0:
            self.player.seek(int(length * self.position_slider.value() / 1000))

    def _step_queue(self, step: int) -> None:
        paths = self.playlist.paths()
        current = self.playlist.current_path() or (
            str(self.player.current_path) if self.player.current_path else None
        )
        if not paths:
            return
        try:
            index = paths.index(current) if current else 0
        except ValueError:
            index = 0
        self.play_path(paths[(index + step) % len(paths)])

    def remove_selected(self) -> None:
        for item in self.playlist.list_widget.selectedItems():
            self.playlist.list_widget.takeItem(self.playlist.list_widget.row(item))

    def save_playlist(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save playlist", "playlist.m3u8", "M3U8 playlists (*.m3u8)"
        )
        if not path:
            return
        try:
            Path(path).write_text(
                "#EXTM3U\n" + "\n".join(self.playlist.paths()) + "\n", encoding="utf-8"
            )
        except OSError as error:
            self._show_error(f"Could not save playlist: {error}")

    def load_playlist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open playlist", "", "M3U playlists (*.m3u8 *.m3u)")
        if not path:
            return
        try:
            entries = []
            for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                entry = Path(line)
                entries.append(str(entry if entry.is_absolute() else Path(path).parent / entry))
            self.playlist.set_paths(entries)
            if entries:
                self.play_path(entries[0])
        except (OSError, UnicodeError) as error:
            self._show_error(f"Could not read playlist: {error}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self._audio_devices(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.player.set_subtitle_delay(int(self.settings.value("subtitle_delay", 0)))
            self.player.set_video_output(str(self.settings.value("audio_device", "")))
            self.player.set_subtitle_size(int(self.settings.value("subtitle_size", 22)))
            self.statusBar().showMessage(
                "Subtitle font size applies to media opened from now on.", 5000
            )
            self._refresh_shortcuts()

    def _audio_devices(self) -> list[tuple[str, str]]:
        devices = []
        device_list = None
        try:
            device_list = self.player._player.audio_output_device_enum()
            device = device_list
            while device:
                item = device.contents
                identifier = item.device.decode("utf-8", errors="replace") if item.device else ""
                description = (
                    item.description.decode("utf-8", errors="replace")
                    if item.description
                    else identifier
                )
                if identifier:
                    devices.append((description, identifier))
                device = item.next
        except Exception:
            LOGGER.exception("Could not enumerate audio output devices")
        finally:
            if device_list:
                vlc.libvlc_audio_output_device_list_release(device_list)
        return devices

    def _refresh_shortcuts(self) -> None:
        settings = (
            (self.open_action, "shortcut_open", "Ctrl+O"),
            (self.play_action, "shortcut_play", "Space"),
            (self.seek_back_action, "shortcut_seek_back", "Left"),
            (self.seek_forward_action, "shortcut_seek_forward", "Right"),
            (self.mute_action, "shortcut_mute", "M"),
            (self.fullscreen_action, "shortcut_fullscreen", "F"),
            (self.stop_action, "shortcut_stop", "S"),
            (self.previous_action, "shortcut_previous", "Ctrl+Left"),
            (self.next_action, "shortcut_next", "Ctrl+Right"),
            (self.exit_fullscreen_action, "shortcut_exit_fullscreen", "Escape"),
        )
        for action, key, default in settings:
            action.setShortcut(QKeySequence(self.settings.value(key, default)))

    def _toggle_pip(self) -> None:
        if not self._pip:
            self._normal_geometry = self.saveGeometry()
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.resize(560, 340)
            self.show()
            self._pip = True
            self.pip_button.setText("Exit PiP")
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            if self._normal_geometry:
                self.restoreGeometry(self._normal_geometry)
            self.show()
            self._pip = False
            self.pip_button.setText("PiP")

    def _add_recent(self, path: str) -> None:
        recent = _read_string_list_setting(self.settings, "recent_files")
        values = [str(Path(path).resolve())] + [item for item in recent if item != str(Path(path).resolve())]
        self.settings.setValue("recent_files", json.dumps(values[:10]))
        self._refresh_recent_menu()

    def _refresh_recent_menu(self) -> None:
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        recent = _read_string_list_setting(self.settings, "recent_files")
        for path in recent:
            if Path(path).is_file():
                action = self.recent_menu.addAction(Path(path).name)
                action.setToolTip(path)
                action.triggered.connect(lambda checked=False, value=path: self.play_path(value))
        if not self.recent_menu.actions():
            self.recent_menu.addAction("(No recent files)").setEnabled(False)

    def _clear_recent(self) -> None:
        self.settings.setValue("recent_files", "[]")
        self._refresh_recent_menu()

    def _restore_state(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        queue = _read_string_list_setting(self.settings, "queue")
        self.playlist.set_paths(queue)
        self.volume_slider.setValue(int(self.settings.value("volume", 100)))
        if self.volume_slider.value() > 0:
            self._last_unmuted_volume = self.volume_slider.value()
        preset = str(self.settings.value("equalizer_preset", "Flat"))
        if self.equalizer_combo.findText(preset) >= 0:
            self.equalizer_combo.setCurrentText(preset)

    def closeEvent(self, event) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("queue", json.dumps(self.playlist.paths()))
        self.settings.setValue("volume", self.volume_slider.value())
        self.player.close()
        super().closeEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self._handle_dropped_paths(paths)
        if paths:
            self.playlist.add_paths(paths)
            event.acceptProposedAction()

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 8000)
        LOGGER.error("%s", message)

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        seconds = max(0, milliseconds // 1000)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60:02d}:{seconds % 60:02d}"


class EqualizerDialog(QDialog):
    def __init__(self, equalizer, parent=None) -> None:
        super().__init__(parent)
        self.equalizer = equalizer
        self.setWindowTitle("10-band equalizer")
        self.setMinimumWidth(560)
        self.enabled_toggle = QCheckBox("Enable equalizer")
        self.enabled_toggle.setChecked(equalizer.enabled)
        self.enabled_toggle.toggled.connect(equalizer.set_enabled)
        row = QHBoxLayout()
        self.sliders: list[QSlider] = []
        self.value_labels: list[QLabel] = []
        for index, frequency in enumerate(EQUALIZER_BANDS):
            column = QVBoxLayout()
            label = QLabel("0.0 dB")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-200, 200)
            slider.setTickInterval(50)
            slider.setValue(round(equalizer.bands[index] * 10))
            slider.valueChanged.connect(
                lambda value, band=index: self._set_band(band, value)
            )
            column.addWidget(label)
            column.addWidget(slider, 1, Qt.AlignmentFlag.AlignHCenter)
            title = QLabel(f"{frequency} Hz")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column.addWidget(title)
            row.addLayout(column)
            self.sliders.append(slider)
            self.value_labels.append(label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.enabled_toggle)
        layout.addLayout(row, 1)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.enabled_toggle.setChecked(self.equalizer.enabled)
        for index, gain in enumerate(self.equalizer.bands):
            slider = self.sliders[index]
            slider.blockSignals(True)
            slider.setValue(round(gain * 10))
            slider.blockSignals(False)
            self.value_labels[index].setText(f"{gain:+.1f} dB")

    def _set_band(self, index: int, value: int) -> None:
        gain = value / 10.0
        self.value_labels[index].setText(f"{gain:+.1f} dB")
        try:
            self.equalizer.set_band(index, gain)
            self.equalizer.set_enabled(True)
            if not self.enabled_toggle.isChecked():
                self.enabled_toggle.setChecked(True)
        except (RuntimeError, ValueError) as error:
            self.parent()._show_error(str(error))
