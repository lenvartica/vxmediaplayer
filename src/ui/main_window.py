"""Main VxPlayer window and playback controls."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import vlc
from PyQt6.QtCore import (
    QEvent,
    QPoint,
    QProcess,
    QSize,
    Qt,
    QSettings,
    QThread,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QMouseEvent, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QDoubleSpinBox,
    QSlider,
    QSplitter,
    QStatusBar,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from engine.equalizer import PRESETS
from engine.player import Player, SUPPORTED_MEDIA, SUBTITLE_SUFFIXES
from ui.playlist_widget import PlaylistWidget
from ui.settings_dialog import SettingsDialog
from ui.windows_integration import (
    WindowsGlobalHotkeys,
    set_keep_awake,
    set_startup_registration,
)
from ui.update_checker import UpdateWorker

LOGGER = logging.getLogger(__name__)
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
MEDIA_FILTER = "Media files (" + " ".join(f"*{suffix}" for suffix in sorted(SUPPORTED_MEDIA)) + ")"
EQUALIZER_BANDS = ("60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k")


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
        self.setToolTip(
            "Click the center to play or pause; click the left or right side to skip 10 seconds."
        )

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
            edge = self.width() * 0.25
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
        self._fullscreen_ui_active = False
        self._fullscreen_layout_state: tuple[tuple[int, int, int, int], int] | None = None
        self._fullscreen_visibility_state: tuple[bool, bool, bool] | None = None
        self._fullscreen_splitter_sizes: list[int] | None = None
        self._fullscreen_splitter_handle_width: int | None = None
        self._last_position_update = 0.0
        self._last_player_state = ""
        self._loop_a: int | None = None
        self._loop_b: int | None = None
        self._resume_pending: tuple[str, int] | None = None
        self._last_resume_save = 0.0
        self._resume_positions = self._read_resume_positions()
        self._quit_requested = False
        self._keep_awake_enabled = (
            self.settings.value("keep_awake", "false") in (True, "true", "1")
        )
        self._keep_awake_active = False
        self._update_thread: QThread | None = None
        self._update_worker: UpdateWorker | None = None
        self._pending_update_download: dict | None = None
        self._silent_update_check = False
        self._close_after_update = False
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
        self.player.set_subtitle_style(
            str(self.settings.value("subtitle_color", "#FFFFFF")),
            int(self.settings.value("subtitle_margin", 24)),
        )
        self.player.set_audio_delay(int(self.settings.value("audio_delay", 0)))
        self.player.set_rotation(int(self.settings.value("video_rotation", 0)))
        self.equalizer_dialog = EqualizerDialog(self.player.equalizer, self)
        self._create_actions()
        self._create_menus()
        self._restore_state()
        self._init_system_tray()
        application = QApplication.instance()
        if application is not None:
            self._global_hotkeys = WindowsGlobalHotkeys(application)
            self._configure_global_hotkeys()
        if sys.platform == "win32":
            QTimer.singleShot(4000, self._check_for_updates_silently)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        self.root_layout = outer
        outer.setContentsMargins(18, 14, 18, 16)
        self.header_widget = QWidget()
        header = QHBoxLayout(self.header_widget)
        brand = QLabel("VxPlayer")
        brand.setObjectName("brand")
        self.track_label = QLabel("Ready when you are")
        self.track_label.setObjectName("trackLabel")
        header.addWidget(brand)
        header.addSpacing(20)
        header.addWidget(self.track_label, 1)
        self.open_button = QPushButton("Open media")
        self.open_button.setObjectName("primaryButton")
        self.subtitle_button = QPushButton("Subtitles")
        header.addWidget(self.subtitle_button)
        header.addWidget(self.open_button)
        outer.addWidget(self.header_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter = splitter
        self.video_surface = VideoSurface()
        self.playlist = PlaylistWidget()
        self.playlist.setMinimumWidth(180)
        splitter.addWidget(self.video_surface)
        splitter.addWidget(self.playlist)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([1040, 204])
        outer.addWidget(splitter, 1)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_label = QLabel("00:00 / 00:00")
        self.seek_widget = QWidget()
        seek_row = QHBoxLayout(self.seek_widget)
        seek_row.addWidget(self.position_slider, 1)
        seek_row.addWidget(self.position_label)
        outer.addWidget(self.seek_widget)

        self.transport_widget = QWidget()
        controls = QHBoxLayout(self.transport_widget)
        self.previous_button = QPushButton()
        self.previous_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward)
        )
        self.previous_button.setText("")
        self.previous_button.setToolTip("Previous item (Ctrl+Left)")
        self.previous_button.setAccessibleName("Previous item")
        self.seek_back_button = QPushButton()
        self.seek_back_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward)
        )
        self.seek_back_button.setText("")
        self.seek_back_button.setToolTip("Back 10 seconds (Left)")
        self.seek_back_button.setAccessibleName("Back 10 seconds")
        self.play_button = QPushButton()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.play_button.setText("")
        self.play_button.setToolTip("Play or pause (Space)")
        self.play_button.setAccessibleName("Play or pause")
        self.play_button.setObjectName("primaryButton")
        self.next_button = QPushButton()
        self.next_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward)
        )
        self.next_button.setText("")
        self.next_button.setToolTip("Next item (Ctrl+Right)")
        self.next_button.setAccessibleName("Next item")
        self.seek_forward_button = QPushButton()
        self.seek_forward_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward)
        )
        self.seek_forward_button.setText("")
        self.seek_forward_button.setToolTip("Forward 10 seconds (Right)")
        self.seek_forward_button.setAccessibleName("Forward 10 seconds")
        self.stop_button = QPushButton()
        self.stop_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        )
        self.stop_button.setText("")
        self.stop_button.setToolTip("Stop playback (S)")
        self.stop_button.setAccessibleName("Stop playback")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x", "3.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.equalizer_combo = QComboBox()
        self.equalizer_combo.addItems(PRESETS)
        self.equalizer_button = QPushButton()
        self.equalizer_button.setIcon(
            QIcon(_svg_pixmap(ASSET_DIR / "equalizer.svg", 24))
        )
        self.equalizer_button.setToolTip("Equalizer bands")
        self.equalizer_button.setAccessibleName("Equalizer bands")
        self.volume_label = QLabel("100%")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 300)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.setToolTip(
            "0–300% output gain. Start low; high volume can damage hearing or distort audio."
        )
        self.mute_button = QPushButton()
        self.mute_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
        )
        self.mute_button.setToolTip("Mute or restore volume (M)")
        self.mute_button.setAccessibleName("Mute")
        self.pip_button = QPushButton()
        self.pip_button.setIcon(QIcon(_svg_pixmap(ASSET_DIR / "pip.svg", 24)))
        self.pip_button.setToolTip("Enter picture-in-picture")
        self.pip_button.setAccessibleName("Enter picture-in-picture")
        for button in (
            self.previous_button,
            self.seek_back_button,
            self.seek_forward_button,
            self.next_button,
            self.stop_button,
            self.mute_button,
            self.equalizer_button,
            self.pip_button,
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
        outer.addWidget(self.transport_widget)
        self.audio_controls_widget = QWidget()
        audio_controls = QHBoxLayout(self.audio_controls_widget)
        for widget in (
            self.equalizer_combo,
            self.equalizer_button,
            self.mute_button,
            self.volume_label,
            self.volume_slider,
        ):
            audio_controls.addWidget(widget)
        audio_controls.addStretch(1)
        outer.addWidget(self.audio_controls_widget)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(
            "Click the video center to play or pause; click the left or right side to skip 10 seconds."
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
        self.check_updates_action = QAction("Check for updates...", self)
        self.check_updates_action.triggered.connect(self._check_for_updates)
        self.frame_step_action = QAction("Next frame", self)
        self.frame_step_action.setShortcut(QKeySequence("E"))
        self.frame_step_action.triggered.connect(lambda checked=False: self.player.next_frame())
        self.slower_action = QAction("Slow down", self)
        self.slower_action.triggered.connect(lambda: self._change_rate(-1))
        self.faster_action = QAction("Speed up", self)
        self.faster_action.triggered.connect(lambda: self._change_rate(1))
        self.mark_a_action = QAction("Set A point", self)
        self.mark_a_action.triggered.connect(self._mark_loop_a)
        self.mark_b_action = QAction("Set B point", self)
        self.mark_b_action.triggered.connect(self._mark_loop_b)
        self.clear_ab_action = QAction("Clear A-B repeat", self)
        self.clear_ab_action.triggered.connect(self._clear_ab_repeat)
        self.loop_current_action = QAction("Repeat current video", self)
        self.loop_current_action.setCheckable(True)
        self.repeat_playlist_action = QAction("Repeat playlist", self)
        self.repeat_playlist_action.setCheckable(True)
        self.snapshot_action = QAction("Capture frame...", self)
        self.snapshot_action.triggered.connect(self._capture_frame)
        self.video_adjust_action = QAction("Video adjustments...", self)
        self.video_adjust_action.triggered.connect(self._video_adjustments)
        self.always_on_top_action = QAction("Always on top", self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.triggered.connect(self._set_always_on_top)
        self.audio_tracks_menu = QMenu("Audio tracks", self)
        self.subtitle_tracks_menu = QMenu("Subtitle tracks", self)
        self.video_tracks_menu = QMenu("Video tracks", self)
        for menu, kind in (
            (self.audio_tracks_menu, "audio"),
            (self.subtitle_tracks_menu, "subtitle"),
            (self.video_tracks_menu, "video"),
        ):
            menu.aboutToShow.connect(lambda track_kind=kind: self._populate_tracks(track_kind))
        for action in (
            self.open_action, self.play_action, self.seek_back_action,
            self.seek_forward_action, self.mute_action, self.fullscreen_action,
            self.stop_action, self.previous_action, self.next_action,
            self.exit_fullscreen_action, self.frame_step_action,
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
        playback_menu = self.menuBar().addMenu("Playback")
        for action in (
            self.slower_action, self.faster_action, self.frame_step_action,
            self.mark_a_action, self.mark_b_action, self.clear_ab_action,
        ):
            playback_menu.addAction(action)
        playback_menu.addSeparator()
        playback_menu.addAction(self.loop_current_action)
        playback_menu.addAction(self.repeat_playlist_action)
        video_menu = self.menuBar().addMenu("Video")
        video_menu.addAction(self.video_adjust_action)
        video_menu.addAction(self.always_on_top_action)
        video_menu.addAction(self.snapshot_action)
        audio_menu = self.menuBar().addMenu("Audio")
        audio_menu.addMenu(self.audio_tracks_menu)
        audio_menu.addAction(
            "Stereo", lambda checked=False: self._set_audio_channel(vlc.AudioOutputChannel.Stereo)
        )
        audio_menu.addAction(
            "Reverse stereo",
            lambda checked=False: self._set_audio_channel(vlc.AudioOutputChannel.RStereo),
        )
        audio_menu.addAction(
            "Left channel only",
            lambda checked=False: self._set_audio_channel(vlc.AudioOutputChannel.Left),
        )
        audio_menu.addAction(
            "Right channel only",
            lambda checked=False: self._set_audio_channel(vlc.AudioOutputChannel.Right),
        )
        audio_menu.addAction(
            "Dolby surround",
            lambda checked=False: self._set_audio_channel(vlc.AudioOutputChannel.Dolbys),
        )
        subtitles_menu = self.menuBar().addMenu("Subtitles")
        subtitles_menu.addMenu(self.subtitle_tracks_menu)
        subtitles_menu.addAction("Load external subtitles...", self.open_subtitle)
        tracks_menu = self.menuBar().addMenu("Tracks")
        tracks_menu.addMenu(self.video_tracks_menu)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self.check_updates_action)
        help_menu.addSeparator()
        help_menu.addAction(self.shortcut_help_action)

    def _check_for_updates(self) -> None:
        if sys.platform != "win32":
            QMessageBox.information(
                self,
                "VxPlayer updates",
                "In-app installer updates are available for Windows. "
                "Check GitHub Releases for updates on this platform.",
            )
            return
        self._silent_update_check = False
        self.statusBar().showMessage("Checking GitHub Releases for VxPlayer updates...")
        self._start_update_task("check")

    def _check_for_updates_silently(self) -> None:
        if self.isVisible() and not self._quit_requested:
            self._silent_update_check = True
            self._start_update_task("check")

    def _start_update_task(self, operation: str, update: dict | None = None) -> None:
        if self._update_thread is not None and self._update_thread.isRunning():
            return
        thread = QThread(self)
        worker = UpdateWorker(operation, update)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._update_task_completed)
        worker.failed.connect(self._update_task_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._update_thread_finished)
        self._update_thread = thread
        self._update_worker = worker
        thread.start()

    @pyqtSlot(str, object)
    def _update_task_completed(self, operation: str, result: object) -> None:
        if operation == "check":
            if result is None:
                if not self._silent_update_check:
                    QMessageBox.information(
                        self,
                        "VxPlayer is up to date",
                        "You already have the latest VxPlayer build.",
                    )
                    self.statusBar().showMessage("VxPlayer is up to date.", 5000)
                self._silent_update_check = False
                return
            self._silent_update_check = False
            if self._close_after_update:
                return
            update = result
            version = update["version"]
            channel = "continuous build" if update.get("prerelease") else "release"
            action = (
                "Download and apply only the changed app files?"
                if update.get("kind") == "incremental"
                else "Download the one-time setup to install all modules?"
            )
            answer = QMessageBox.question(
                self,
                "VxPlayer update available",
                f"VxPlayer {version} ({channel}) is available.\n\n"
                f"{action}\nThe update files will be verified before installation.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._pending_update_download = update
                self.statusBar().showMessage(f"Preparing VxPlayer {version} update...")
            return

        if not isinstance(result, dict):
            self._show_error("The verified update result is invalid.")
            return
        if result.get("kind") == "installer":
            installer_path = result.get("path")
            if not isinstance(installer_path, str):
                self._show_error("The verified installer path is invalid.")
                return
            process = QProcess(self)
            process.setProgram(installer_path)
            started = bool(process.startDetached())
        elif result.get("kind") == "incremental":
            plan_path = result.get("plan")
            if not isinstance(plan_path, str):
                self._show_error("The verified incremental update plan is invalid.")
                return
            started = self._start_incremental_updater(plan_path)
        else:
            self._show_error("The verified update has an unknown installation mode.")
            return
        if not started:
            self._show_error("The verified VxPlayer update could not be started.")
            return
        self._quit_requested = True
        if self.tray_icon is not None:
            self.tray_icon.hide()
        QTimer.singleShot(0, self.close)

    def _start_incremental_updater(self, plan_path: str) -> bool:
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            self._show_error("Incremental updates require the installed Windows version of VxPlayer.")
            return False
        install_root = Path(sys.executable).resolve().parent
        updater = install_root / "VxPlayerUpdater.exe"
        if not updater.is_file():
            self._show_error("The installed update helper is missing. Run the full setup once to repair VxPlayer.")
            return False
        helper_directory = Path(tempfile.mkdtemp(prefix="VxPlayer-Update-"))
        helper_copy = helper_directory / updater.name
        try:
            shutil.copy2(updater, helper_copy)
        except OSError as error:
            shutil.rmtree(helper_directory, ignore_errors=True)
            self._show_error(f"Could not prepare the update helper: {error}")
            return False

        arguments = ["--apply", plan_path, str(os.getpid()), str(install_root)]
        if self.player.current_path is not None:
            arguments.append(str(self.player.current_path))
        process = QProcess(self)
        process.setProgram(str(helper_copy))
        process.setArguments(arguments)
        started = bool(process.startDetached())
        if not started:
            shutil.rmtree(helper_directory, ignore_errors=True)
        return started

    @pyqtSlot(str)
    def _update_task_failed(self, message: str) -> None:
        if self._silent_update_check:
            self._silent_update_check = False
            LOGGER.warning("Automatic update check failed: %s", message)
            return
        QMessageBox.warning(
            self,
            "VxPlayer update problem",
            f"VxPlayer could not complete the update task:\n\n{message}",
        )
        self.statusBar().showMessage("VxPlayer update check failed.", 7000)

    def _update_thread_finished(self) -> None:
        thread = self.sender()
        if thread is not self._update_thread:
            return
        self._update_thread = None
        self._update_worker = None
        thread.deleteLater()
        update = self._pending_update_download
        if update is not None:
            self._pending_update_download = None
            self.statusBar().showMessage(
                f"Downloading and verifying changed files for VxPlayer {update['version']}..."
            )
            self._start_update_task("download", update)
            return
        if self._close_after_update:
            self._close_after_update = False
            QTimer.singleShot(0, self.close)

    def _init_system_tray(self) -> None:
        self.tray_icon: QSystemTrayIcon | None = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        tray_menu = QMenu(self)
        tray_menu.addAction("Show VxPlayer", self._show_from_tray)
        tray_menu.addAction("Play / pause", self._toggle_play)
        tray_menu.addAction("Previous track", lambda checked=False: self._step_queue(-1))
        tray_menu.addAction("Next track", lambda checked=False: self._step_queue(1))
        tray_menu.addSeparator()
        tray_menu.addAction("Quit VxPlayer", self._quit_from_tray)
        self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
        self.tray_icon.setToolTip("VxPlayer")
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self._show_from_tray()

    def _quit_from_tray(self) -> None:
        self._quit_requested = True
        self.close()

    def _configure_global_hotkeys(self) -> None:
        if not hasattr(self, "_global_hotkeys"):
            return
        if self.settings.value("global_hotkeys", "false") not in (True, "true", "1"):
            self._global_hotkeys.unregister()
            return
        callbacks = {
            "play": self._toggle_play,
            "next": lambda: self._step_queue(1),
            "previous": lambda: self._step_queue(-1),
        }
        shortcuts = {
            key: str(self.settings.value(f"global_shortcut_{key}", default))
            for key, default in (
                ("play", "Ctrl+Alt+Space"),
                ("next", "Ctrl+Alt+Right"),
                ("previous", "Ctrl+Alt+Left"),
            )
        }
        try:
            conflicts = self._global_hotkeys.register(callbacks, shortcuts)
        except (OSError, RuntimeError, ValueError) as error:
            self._show_error(str(error))
        else:
            if conflicts:
                self.statusBar().showMessage(
                    "Some hardware media keys are already used by another app: "
                    + ", ".join(conflicts),
                    8000,
                )

    def _update_keep_awake(self, playing: bool) -> None:
        should_keep_awake = self._keep_awake_enabled and playing
        if should_keep_awake == self._keep_awake_active:
            return
        try:
            set_keep_awake(should_keep_awake)
        except (OSError, RuntimeError) as error:
            self._keep_awake_enabled = False
            self.settings.setValue("keep_awake", False)
            self._show_error(str(error))
            return
        self._keep_awake_active = should_keep_awake

    def open_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open media", "", f"{MEDIA_FILTER};;All files (*)"
        )
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
        media = [
            path
            for path in paths
            if Path(path).suffix.lower() not in SUBTITLE_SUFFIXES and Path(path).is_file()
        ]
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
        self._set_fullscreen_ui(self.isFullScreen())

    def _exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self._toggle_fullscreen()

    def _set_fullscreen_ui(self, fullscreen: bool) -> None:
        if fullscreen == self._fullscreen_ui_active:
            return
        self._fullscreen_ui_active = fullscreen
        if fullscreen:
            margins = self.root_layout.contentsMargins()
            self._fullscreen_layout_state = (
                (margins.left(), margins.top(), margins.right(), margins.bottom()),
                self.root_layout.spacing(),
            )
            self._fullscreen_visibility_state = (
                self.playlist.isVisible(),
                self.menuBar().isVisible(),
                self.statusBar().isVisible(),
            )
            self._fullscreen_splitter_sizes = self.splitter.sizes()
            self._fullscreen_splitter_handle_width = self.splitter.handleWidth()
            self.header_widget.hide()
            self.seek_widget.hide()
            self.transport_widget.hide()
            self.audio_controls_widget.hide()
            self.playlist.hide()
            self.menuBar().hide()
            self.statusBar().hide()
            self.splitter.setHandleWidth(0)
            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.root_layout.setSpacing(0)
            self.video_surface.setStyleSheet("border: 0;")
            return

        if self._fullscreen_layout_state is not None:
            margins, spacing = self._fullscreen_layout_state
            self.root_layout.setContentsMargins(*margins)
            self.root_layout.setSpacing(spacing)
        if self._fullscreen_splitter_handle_width is not None:
            self.splitter.setHandleWidth(self._fullscreen_splitter_handle_width)
        self.video_surface.setStyleSheet("")
        self.header_widget.show()
        self.seek_widget.show()
        self.transport_widget.show()
        self.audio_controls_widget.show()
        if self._fullscreen_visibility_state is not None:
            playlist_visible, menu_visible, status_visible = self._fullscreen_visibility_state
            self.playlist.setVisible(playlist_visible)
            self.menuBar().setVisible(menu_visible)
            self.statusBar().setVisible(status_visible)
        if self._fullscreen_splitter_sizes is not None:
            self.splitter.setSizes(self._fullscreen_splitter_sizes)

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
        icon = (
            QStyle.StandardPixmap.SP_MediaVolumeMuted
            if value == 0
            else QStyle.StandardPixmap.SP_MediaVolume
        )
        self.mute_button.setIcon(self.style().standardIcon(icon))
        self.mute_button.setAccessibleName("Unmute" if value == 0 else "Mute")
        if value > 0:
            self._last_unmuted_volume = value

    def _set_rate(self, rate: float) -> None:
        self.player.set_rate(rate)

    def _change_rate(self, direction: int) -> None:
        index = max(0, min(self.speed_combo.count() - 1, self.speed_combo.currentIndex() + direction))
        self.speed_combo.setCurrentIndex(index)

    def _mark_loop_a(self) -> None:
        self._loop_a = self.player.current_time_ms
        self._loop_b = None
        self.statusBar().showMessage(f"A-B repeat start: {self._format_time(self._loop_a)}", 4000)

    def _mark_loop_b(self) -> None:
        position = self.player.current_time_ms
        if self._loop_a is None or position <= self._loop_a:
            self._show_error("Set a valid A point before setting the B point.")
            return
        self._loop_b = position
        self.statusBar().showMessage(
            f"A-B repeat: {self._format_time(self._loop_a)} – {self._format_time(self._loop_b)}",
            5000,
        )

    def _clear_ab_repeat(self) -> None:
        self._loop_a = None
        self._loop_b = None
        self.statusBar().showMessage("A-B repeat cleared.", 3000)

    def _capture_frame(self) -> None:
        if not self.player.current_path:
            self._show_error("Open a video before capturing a frame.")
            return
        suggested = self.player.current_path.with_suffix(".png")
        path, _ = QFileDialog.getSaveFileName(
            self, "Capture frame", str(suggested), "PNG image (*.png);;JPEG image (*.jpg *.jpeg)"
        )
        if path:
            try:
                self.player.take_snapshot(path)
                self.statusBar().showMessage(f"Frame saved to {path}", 5000)
            except (OSError, RuntimeError) as error:
                self._show_error(str(error))

    def _populate_tracks(self, kind: str) -> None:
        menu = {
            "audio": self.audio_tracks_menu,
            "subtitle": self.subtitle_tracks_menu,
            "video": self.video_tracks_menu,
        }[kind]
        menu.clear()
        try:
            tracks = self.player.tracks(kind)
            current = self.player.current_track(kind)
        except Exception as error:
            LOGGER.debug("Could not populate %s tracks", kind, exc_info=True)
            menu.addAction(f"Track list unavailable: {error}").setEnabled(False)
            return
        if kind == "subtitle":
            tracks.insert(0, (-1, "Disabled"))
        for track_id, label in tracks:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(track_id == current)
            action.triggered.connect(
                lambda checked=False, selected=track_id, track_kind=kind:
                self._select_track(track_kind, selected)
            )
        if not tracks:
            menu.addAction("No tracks available").setEnabled(False)

    def _select_track(self, kind: str, track_id: int) -> None:
        try:
            self.player.select_track(kind, track_id)
        except (RuntimeError, ValueError) as error:
            self._show_error(str(error))

    def _set_audio_channel(self, channel: int) -> None:
        try:
            self.player.set_audio_channel(channel)
        except RuntimeError as error:
            self._show_error(str(error))

    def _video_adjustments(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Video adjustments")
        form = QFormLayout(dialog)
        controls: dict[str, QDoubleSpinBox] = {}
        for label, key, maximum in (
            ("Brightness", "brightness", 2.0),
            ("Contrast", "contrast", 2.0),
            ("Saturation", "saturation", 3.0),
            ("Gamma", "gamma", 10.0),
        ):
            control = QDoubleSpinBox()
            control.setRange(0.0, maximum)
            control.setSingleStep(0.05)
            control.setValue(float(self.settings.value(f"video_{key}", 1.0)))
            controls[key] = control
            form.addRow(label, control)
        aspect = QComboBox()
        aspect.addItems(["Default", "16:9", "4:3", "1:1", "2.35:1"])
        aspect.setCurrentText(str(self.settings.value("video_aspect", "Default")))
        form.addRow("Aspect ratio", aspect)
        zoom = QComboBox()
        zoom.addItems(["1.0x", "1.25x", "1.5x", "2.0x"])
        zoom.setCurrentText(str(self.settings.value("video_zoom", "1.0x")))
        form.addRow("Zoom", zoom)
        rotation = QComboBox()
        rotation.addItems(["0°", "90°", "180°", "270°"])
        rotation.setCurrentText(f"{int(self.settings.value('video_rotation', 0))}°")
        form.addRow("Rotation (reopens media)", rotation)
        deinterlace = QComboBox()
        deinterlace.addItems(["Off", "yadif", "yadif2x", "blend", "bob", "linear"])
        deinterlace.setCurrentText(str(self.settings.value("deinterlace", "Off")))
        form.addRow("Deinterlacing", deinterlace)
        crop = QComboBox()
        crop.addItems(["None", "16:9", "4:3", "1:1", "2.35:1"])
        crop.setCurrentText(str(self.settings.value("video_crop", "None")))
        form.addRow("Crop", crop)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            for key, control in controls.items():
                value = control.value()
                self.player.set_video_adjustment(key, value)
                self.settings.setValue(f"video_{key}", value)
            ratio = "" if aspect.currentText() == "Default" else aspect.currentText()
            self.player.set_aspect_ratio(ratio)
            self.player.set_video_scale(float(zoom.currentText().rstrip("x")))
            self.player.set_rotation(int(rotation.currentText().rstrip("°")))
            crop_value = "" if crop.currentText() == "None" else crop.currentText()
            self.player.set_crop(crop_value)
            self.player.set_deinterlace(
                "" if deinterlace.currentText() == "Off" else deinterlace.currentText()
            )
            self.settings.setValue("video_aspect", aspect.currentText())
            self.settings.setValue("video_zoom", zoom.currentText())
            self.settings.setValue("video_rotation", rotation.currentText().rstrip("°"))
            self.settings.setValue("video_crop", crop.currentText())
            self.settings.setValue("deinterlace", deinterlace.currentText())
            self.settings.setValue("video_adjustment_configured", True)
        except (RuntimeError, ValueError) as error:
            self._show_error(str(error))

    def _set_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()

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
        if self._loop_a is not None and self._loop_b is not None and position >= self._loop_b:
            self.player.seek(self._loop_a)
        if (
            self.player.current_path
            and position > 0
            and time.monotonic() - self._last_resume_save >= 10
        ):
            current_path = str(self.player.current_path)
            if length > 0 and position >= length - 3000:
                self._resume_positions.pop(current_path, None)
            else:
                self._resume_positions[current_path] = position
            self._save_resume_positions()
            self._last_resume_save = time.monotonic()
        now = time.monotonic()
        if now - self._last_position_update >= 0.8:
            self.position_label.setText(f"{self._format_time(position)} / {self._format_time(length)}")
            self._last_position_update = now

    def _update_state(self, state: str) -> None:
        playing = state == "playing"
        self._update_keep_awake(playing)
        if state == "error" and self._last_player_state != "error":
            name = self.player.current_path.name if self.player.current_path else "media"
            self._show_error(
                f"LibVLC could not play {name}. "
                "The file or one of its codecs may be unsupported."
            )
        icon = (
            QStyle.StandardPixmap.SP_MediaPause
            if playing
            else QStyle.StandardPixmap.SP_MediaPlay
        )
        self.play_button.setIcon(self.style().standardIcon(icon))
        self.play_button.setToolTip(
            "Pause playback (Space)" if playing else "Play or pause (Space)"
        )
        self.play_button.setAccessibleName("Pause" if playing else "Play")
        if (
            state == "ended"
            and self._last_player_state != "ended"
        ):
            if self.loop_current_action.isChecked():
                if self.player.current_path:
                    current_path = str(self.player.current_path)
                    self._resume_positions.pop(current_path, None)
                    self.player.open(current_path)
            elif self.repeat_playlist_action.isChecked() and self.playlist.paths():
                self._step_queue(1)
        self._last_player_state = state
        if state == "playing" and self._resume_pending:
            path, position = self._resume_pending
            self._resume_pending = None
            if position > 5000 and self.player.current_path and str(self.player.current_path) == path:
                QTimer.singleShot(500, lambda: self.player.seek(position))
                self.statusBar().showMessage("Resumed from the last position.", 3500)

    def _media_changed(self, path: str) -> None:
        self.track_label.setText(Path(path).name)
        self.setWindowTitle(f"{Path(path).name} — VxPlayer")
        self.player.set_subtitle_delay(int(self.settings.value("subtitle_delay", 0)))
        self._loop_a = None
        self._loop_b = None
        resume = self._resume_positions.get(str(Path(path)))
        self._resume_pending = (str(Path(path)), resume) if resume else None
        QTimer.singleShot(600, self._apply_video_settings)

    def _apply_video_settings(self) -> None:
        if not self.player.current_path:
            return
        try:
            ratio = str(self.settings.value("video_aspect", "Default"))
            self.player.set_aspect_ratio("" if ratio == "Default" else ratio)
            self.player.set_video_scale(
                float(str(self.settings.value("video_zoom", "1.0x")).rstrip("x"))
            )
            crop = str(self.settings.value("video_crop", "None"))
            self.player.set_crop("" if crop == "None" else crop)
            deinterlace = str(self.settings.value("deinterlace", "Off"))
            self.player.set_deinterlace("" if deinterlace == "Off" else deinterlace)
            if self.settings.value("video_adjustment_configured", False) in (True, "true", "1"):
                for key in ("brightness", "contrast", "saturation", "gamma"):
                    self.player.set_video_adjustment(
                        key, float(self.settings.value(f"video_{key}", 1.0))
                    )
        except (RuntimeError, ValueError) as error:
            self._show_error(f"Could not apply saved video settings: {error}")

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
        if current not in paths:
            index = -1 if step > 0 else 0
        else:
            index = paths.index(current)
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
        dialog = SettingsDialog(
            self.settings,
            self._audio_devices(),
            self,
            tray_available=self.tray_icon is not None,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.player.set_subtitle_delay(int(self.settings.value("subtitle_delay", 0)))
            self.player.set_audio_delay(int(self.settings.value("audio_delay", 0)))
            self.player.set_video_output(str(self.settings.value("audio_device", "")))
            self.player.set_subtitle_size(int(self.settings.value("subtitle_size", 22)))
            self.player.set_subtitle_style(
                str(self.settings.value("subtitle_color", "#FFFFFF")),
                int(self.settings.value("subtitle_margin", 24)),
            )
            self._keep_awake_enabled = (
                self.settings.value("keep_awake", "false") in (True, "true", "1")
            )
            if not self._keep_awake_enabled:
                self._update_keep_awake(False)
            if sys.platform == "win32":
                try:
                    set_startup_registration(
                        self.settings.value("start_with_windows", "false")
                        in (True, "true", "1")
                    )
                except (OSError, RuntimeError) as error:
                    self.settings.setValue("start_with_windows", False)
                    self._show_error(f"Could not update Windows startup setting: {error}")
            self.statusBar().showMessage(
                "Subtitle styling applies to media opened from now on.", 5000
            )
            self._configure_global_hotkeys()
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
            self.pip_button.setToolTip("Exit picture-in-picture")
            self.pip_button.setAccessibleName("Exit picture-in-picture")
        else:
            self.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint,
                self.always_on_top_action.isChecked(),
            )
            if self._normal_geometry:
                self.restoreGeometry(self._normal_geometry)
            self.show()
            self._pip = False
            self.pip_button.setToolTip("Enter picture-in-picture")
            self.pip_button.setAccessibleName("Enter picture-in-picture")

    def _add_recent(self, path: str) -> None:
        recent = _read_string_list_setting(self.settings, "recent_files")
        values = [str(Path(path).resolve())] + [item for item in recent if item != str(Path(path).resolve())]
        self.settings.setValue("recent_files", json.dumps(values[:10]))
        self._refresh_recent_menu()

    def _read_resume_positions(self) -> dict[str, int]:
        try:
            value = self.settings.value("resume_positions", "{}")
            entries = value if isinstance(value, dict) else json.loads(str(value))
        except (TypeError, json.JSONDecodeError):
            LOGGER.warning("Ignoring invalid saved playback positions")
            return {}
        if not isinstance(entries, dict):
            return {}
        return {
            path: int(position)
            for path, position in entries.items()
            if isinstance(path, str) and isinstance(position, int) and position > 0
        }

    def _save_resume_positions(self) -> None:
        if len(self._resume_positions) > 100:
            self._resume_positions = dict(list(self._resume_positions.items())[-100:])
        self.settings.setValue(
            "resume_positions", json.dumps(self._resume_positions, ensure_ascii=False)
        )

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
        self.loop_current_action.setChecked(
            self.settings.value("loop_current", "false") in (True, "true", "1")
        )
        self.repeat_playlist_action.setChecked(
            self.settings.value("repeat_playlist", "false") in (True, "true", "1")
        )

    def changeEvent(self, event) -> None:
        if (
            event.type() == QEvent.Type.WindowStateChange
            and hasattr(self, "root_layout")
        ):
            self._set_fullscreen_ui(self.isFullScreen())
        if (
            event.type() == QEvent.Type.WindowStateChange
            and self.isMinimized()
            and self.tray_icon is not None
            and self.settings.value("minimize_to_tray", "false") in (True, "true", "1")
            and not self._quit_requested
        ):
            self.hide()
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        if (
            not self._quit_requested
            and self.tray_icon is not None
            and self.settings.value("minimize_to_tray", "false") in (True, "true", "1")
        ):
            self._persist_state()
            self.hide()
            event.ignore()
            return
        if self._update_thread is not None and self._update_thread.isRunning():
            self._close_after_update = True
            self.statusBar().showMessage("Finishing the current update task before closing...")
            event.ignore()
            return
        self._persist_state()
        if hasattr(self, "_global_hotkeys"):
            self._global_hotkeys.unregister()
        if self._keep_awake_active:
            try:
                set_keep_awake(False)
            except (OSError, RuntimeError):
                LOGGER.exception("Could not restore Windows power state on exit")
            self._keep_awake_active = False
        self.player.close()
        super().closeEvent(event)

    def _persist_state(self) -> None:
        if self.player.current_path and self.player.current_time_ms:
            self._resume_positions[str(self.player.current_path)] = self.player.current_time_ms
        self._save_resume_positions()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("queue", json.dumps(self.playlist.paths()))
        self.settings.setValue("volume", self.volume_slider.value())
        self.settings.setValue("loop_current", self.loop_current_action.isChecked())
        self.settings.setValue("repeat_playlist", self.repeat_playlist_action.isChecked())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.playlist.add_paths(paths)
        self._handle_dropped_paths(paths)
        if paths:
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
