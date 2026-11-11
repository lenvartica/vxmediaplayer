"""LibVLC playback engine with volume, subtitle, and queue helpers."""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Optional

import vlc
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from engine.equalizer import Equalizer

LOGGER = logging.getLogger(__name__)
SUPPORTED_MEDIA = {
    ".mp4", ".mp3", ".m4a", ".mkv", ".avi", ".flac", ".wav", ".aac",
    ".ogg", ".mov", ".wmv", ".webm", ".3gp", ".m4v", ".ts", ".opus",
}
SUBTITLE_SUFFIXES = {".srt", ".vtt", ".ass", ".ssa", ".sub"}


class Player(QObject):
    """Qt-signalling wrapper around a LibVLC media player."""

    position_changed = pyqtSignal(int, int)
    state_changed = pyqtSignal(str)
    media_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    volume_changed = pyqtSignal(int)

    def __init__(self, video_widget: object, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._instance = vlc.Instance(
            "--no-video-title-show",
            "--quiet",
            "--audio-filter=compressor,scaletempo",
            "--compressor-threshold=-10.0",
            "--compressor-ratio=8.0",
            "--compressor-attack=25.0",
            "--compressor-release=100.0",
            "--compressor-knee=2.5",
            "--compressor-makeup-gain=2.0",
        )
        if self._instance is None:
            raise RuntimeError("LibVLC could not be initialized. Install VLC/libvlc.")
        self._player = self._instance.media_player_new()
        self.equalizer = Equalizer(self._player)
        self._video_widget = video_widget
        self._current_path: Optional[Path] = None
        self._volume = 100
        self._native_volume = 100
        self._applied_volume: Optional[int] = None
        self._volume_error_reported = False
        self._subtitle_delay = 0
        self._applied_subtitle_delay: Optional[int] = None
        self._subtitle_size = 22
        self._audio_device_id = ""
        self._applied_audio_device: Optional[str] = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start()
        self._bind_video_surface()
        self.set_volume(100)

    @property
    def current_path(self) -> Optional[Path]:
        return self._current_path

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def subtitle_delay(self) -> int:
        return self._subtitle_delay

    @property
    def duration_ms(self) -> int:
        return max(0, self._player.get_length())

    def _bind_video_surface(self) -> None:
        handle = int(self._video_widget.winId())
        if os.name == "nt":
            self._player.set_hwnd(handle)
        elif sys_platform_is_macos():
            self._player.set_nsobject(handle)
        else:
            self._player.set_xwindow(handle)

    def open(self, path: str | Path, autoplay: bool = True) -> None:
        media_path = Path(path).expanduser().resolve()
        if not media_path.is_file():
            raise FileNotFoundError(f"Media file not found: {media_path}")
        media = self._instance.media_new(str(media_path))
        media.add_option(f":freetype-fontsize={self._subtitle_size}")
        self._player.set_media(media)
        self._current_path = media_path
        self._applied_subtitle_delay = None
        self._subtitle_delay = 0
        self.media_changed.emit(str(media_path))
        self._load_adjacent_subtitle(media_path)
        if autoplay:
            self.play()

    def play(self) -> None:
        result = self._player.play()
        if result == -1:
            self.error_occurred.emit("LibVLC could not start playback.")

    def pause(self) -> None:
        self._player.pause()

    def toggle_play_pause(self) -> None:
        if self._player.is_playing():
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        self._player.stop()

    def seek(self, position_ms: int) -> None:
        if self._player.is_seekable():
            result = self._player.set_time(max(0, int(position_ms)))
            if result == -1:
                LOGGER.debug("LibVLC rejected seek to %s ms", position_ms)

    def set_volume(self, volume: int) -> None:
        """Set output gain from 0 to 300 percent, preserving the full requested range."""
        value = max(0, min(300, int(volume)))
        self._volume = value
        self._volume_error_reported = False
        self._native_volume = min(value, 200)
        boost_db = 20.0 * math.log10(value / 200.0) if value > 200 else 0.0
        try:
            self.equalizer.set_volume_boost(boost_db)
        except RuntimeError as error:
            self.error_occurred.emit(str(error))
        self._apply_volume()
        self.volume_changed.emit(value)

    def set_rate(self, rate: float) -> None:
        if not 0.25 <= rate <= 4.0:
            raise ValueError("Playback speed must be between 0.25x and 4.0x")
        if self._player.set_rate(float(rate)) == -1:
            self.error_occurred.emit("This media or LibVLC build does not support that speed.")

    def set_subtitle(self, path: str | Path) -> None:
        subtitle_path = Path(path).expanduser().resolve()
        if not subtitle_path.is_file() or subtitle_path.suffix.lower() not in SUBTITLE_SUFFIXES:
            raise ValueError("Choose an existing .srt, .vtt, .ass, .ssa, or .sub subtitle file")
        if self._player.add_slave(
            vlc.MediaSlaveType.subtitle, subtitle_path.as_uri(), True
        ) == -1:
            raise RuntimeError(f"LibVLC could not load subtitle: {subtitle_path.name}")

    def set_subtitle_delay(self, delay_ms: int) -> None:
        self._subtitle_delay = max(-5000, min(5000, int(delay_ms)))
        self._applied_subtitle_delay = None

    def set_subtitle_size(self, size: int) -> None:
        if not 12 <= int(size) <= 48:
            raise ValueError("Subtitle font size must be between 12 and 48 pixels")
        self._subtitle_size = int(size)

    def set_video_output(self, output: str) -> None:
        self._audio_device_id = output
        self._applied_audio_device = None

    def _load_adjacent_subtitle(self, media_path: Path) -> None:
        for suffix in sorted(SUBTITLE_SUFFIXES):
            candidate = media_path.with_suffix(suffix)
            if candidate.is_file():
                try:
                    self.set_subtitle(candidate)
                except (RuntimeError, ValueError):
                    LOGGER.exception("Could not load adjacent subtitle %s", candidate)
                break

    def _poll(self) -> None:
        state = self._player.get_state()
        if (
            self._current_path is not None
            and state in (vlc.State.Playing, vlc.State.Paused)
            and self._applied_volume != self._volume
        ):
            self._apply_volume()
        if (
            self._audio_device_id
            and state == vlc.State.Playing
            and self._applied_audio_device != self._audio_device_id
        ):
            self._player.audio_output_device_set(None, self._audio_device_id)
            self._applied_audio_device = self._audio_device_id
        length = max(0, self._player.get_length())
        position = max(0, self._player.get_time())
        if (
            self._applied_subtitle_delay != self._subtitle_delay
            and self._player.video_get_spu() >= 0
        ):
            # LibVLC expects subtitle delay in microseconds; retry after the track appears.
            if self._player.video_set_spu_delay(self._subtitle_delay * 1000) == 0:
                self._applied_subtitle_delay = self._subtitle_delay
        self.position_changed.emit(position, length)
        self.state_changed.emit(str(state).split(".")[-1].lower())

    def _apply_volume(self) -> None:
        if self._player.audio_set_volume(self._native_volume) == 0:
            self._applied_volume = self._volume
            self._volume_error_reported = False
        elif self._current_path is not None and not self._volume_error_reported:
            self._volume_error_reported = True
            self.error_occurred.emit(
                "LibVLC could not apply the requested volume. Its supported range may be lower."
            )

    def close(self) -> None:
        self._poll_timer.stop()
        self._player.stop()
        self._player.release()
        self._instance.release()


def sys_platform_is_macos() -> bool:
    import sys

    return sys.platform == "darwin"
