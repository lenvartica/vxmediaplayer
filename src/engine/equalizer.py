"""10-band equalizer presets backed by LibVLC."""

from __future__ import annotations

from dataclasses import dataclass

import vlc


@dataclass(frozen=True)
class EqualizerPreset:
    name: str
    bands: tuple[float, ...]


PRESETS: dict[str, EqualizerPreset] = {
    "Flat": EqualizerPreset("Flat", (0.0,) * 10),
    "Bass Boost": EqualizerPreset(
        "Bass Boost", (7.0, 6.0, 4.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ),
    "Vocal": EqualizerPreset(
        "Vocal", (-2.0, -1.0, 0.0, 2.0, 4.0, 4.0, 2.0, 1.0, 0.0, -1.0)
    ),
    "Party": EqualizerPreset(
        "Party", (4.0, 3.0, 1.0, 0.0, -1.0, -1.0, 0.0, 1.0, 3.0, 4.0)
    ),
    "Rock": EqualizerPreset(
        "Rock", (5.0, 3.0, -2.0, -4.0, -1.0, 2.0, 5.0, 6.0, 6.0, 6.0)
    ),
    "Pop": EqualizerPreset(
        "Pop", (-1.0, 2.0, 4.0, 4.0, 1.0, -1.0, -1.0, 1.0, 2.0, 2.0)
    ),
}


class Equalizer:
    """Applies named equalizer curves using LibVLC's native audio equalizer."""

    def __init__(self, player: vlc.MediaPlayer) -> None:
        self._player = player
        self._enabled = False
        self._preset = "Flat"
        self._bands = PRESETS["Flat"].bands
        self._volume_boost_db = 0.0

    @property
    def preset_names(self) -> tuple[str, ...]:
        return tuple(PRESETS)

    @property
    def bands(self) -> tuple[float, ...]:
        return self._bands

    @property
    def preset(self) -> str:
        return self._preset

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_preset(self, name: str) -> None:
        if name not in PRESETS:
            raise ValueError(f"Unknown equalizer preset: {name}")
        self._preset = name
        self._bands = PRESETS[name].bands
        if self._enabled:
            self._apply()

    def set_band(self, index: int, gain_db: float) -> None:
        if not 0 <= index < 10:
            raise IndexError("Equalizer band index must be between 0 and 9")
        if not -20.0 <= gain_db <= 20.0:
            raise ValueError("Equalizer gain must be between -20 and 20 dB")
        bands = list(self._bands)
        bands[index] = float(gain_db)
        self._bands = tuple(bands)
        self._preset = "Custom"
        if self._enabled:
            self._apply()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self._apply()

    def set_volume_boost(self, gain_db: float) -> None:
        if not 0.0 <= gain_db <= 6.0:
            raise ValueError("Additional volume gain must be between 0 and 6 dB")
        self._volume_boost_db = float(gain_db)
        self._apply()

    def _apply(self) -> None:
        if not self._enabled and self._volume_boost_db == 0.0:
            if self._player.set_equalizer(None) == -1:
                raise RuntimeError("LibVLC could not disable the equalizer")
            return
        equalizer = vlc.AudioEqualizer()
        try:
            if equalizer.set_preamp(self._volume_boost_db) == -1:
                raise RuntimeError("LibVLC could not apply additional volume gain")
            for index, gain in enumerate(self._bands if self._enabled else (0.0,) * 10):
                if equalizer.set_amp_at_index(gain, index) == -1:
                    raise RuntimeError(f"LibVLC could not configure equalizer band {index + 1}")
            result = self._player.set_equalizer(equalizer)
        finally:
            equalizer.release()
        if result == -1:
            raise RuntimeError("LibVLC could not apply the equalizer")
