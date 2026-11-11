# VxPlayer

**A modern desktop media player by Decan Konnect.** VxPlayer combines a PyQt6 interface with LibVLC playback for a broad range of audio and video formats.

[![Build and release](https://github.com/Decan-Konnect/VxPlayer/actions/workflows/build.yml/badge.svg)](https://github.com/Decan-Konnect/VxPlayer/actions/workflows/build.yml)
[![Deploy GitHub Pages](https://github.com/Decan-Konnect/VxPlayer/actions/workflows/pages.yml/badge.svg)](https://github.com/Decan-Konnect/VxPlayer/actions/workflows/pages.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

- LibVLC playback for MP4, MP3, M4A, MKV, AVI, FLAC, WAV, AAC, OGG, MOV, WMV, WebM, 3GP, M4V, TS, and Opus.
- Dark PyQt6 interface, normalized seeking, playback queue, filtering, drag-and-drop, M3U8 playlists, and recent-file history.
- Volume slider from 0–300%, using LibVLC volume up to 200% and equalizer preamp gain above that. A compressor filter is enabled to reduce peaks; device and plugin limits still apply. High volume can damage hearing.
- Native 10-band equalizer with Bass Boost, Vocal, Party, Flat, Rock, and Pop curves.
- Playback speed from 0.25x to 4x; pitch preservation depends on LibVLC's `scaletempo` plugin.
- Adjacent subtitle detection, SRT/VTT and other LibVLC subtitle files, and subtitle delay adjustment from -5000 to +5000 ms.
- Always-on-top compact picture-in-picture window mode and configurable application keyboard shortcuts.
- No analytics or telemetry in the application.

## Quick start

Python 3.11 or newer and a LibVLC runtime are required. The Windows release workflow bundles LibVLC. Linux builds use system LibVLC.

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

On Linux, install your distribution's VLC/LibVLC packages before launching. If the player reports that LibVLC cannot initialize, verify that the VLC libraries and plugin directory are installed and discoverable. For source runs, install VLC for your operating system.

## Controls

- **Open media** or `Ctrl+O`: choose files; drag files onto the player to add or play them.
- **Space**: play or pause.
- Double-click an item in the queue to play it. Queue items can be reordered, filtered, removed, and saved as `.m3u8`.
- Use the speed and equalizer menus, volume slider, or subtitle button for playback adjustments.
- Settings provides audio device, subtitle delay/font-size preference, and keyboard shortcut configuration. Shortcuts apply while VxPlayer is active; OS-wide global hotkeys are not implemented.

## Project layout

```text
.github/workflows/  Windows/Linux build and GitHub Pages deployment
src/assets/         Dark-mode QSS theme
src/engine/         LibVLC wrapper and equalizer
src/ui/             Player, queue, and settings interfaces
docs/               GitHub Pages product site
requirements.txt    Pinned Python runtime/build dependencies
```

## Builds and deployment

Push a `v*` tag to create Windows x64 and Linux x64 build artifacts and a GitHub Release. Windows packages `libvlc.dll`, `libvlccore.dll`, and VLC plugins into the PyInstaller executable. Linux output is a PyInstaller executable and requires compatible system LibVLC libraries/plugins. The Pages workflow deploys `docs/` from `main`; enable GitHub Pages with the GitHub Actions source in repository settings.

The site currently points to `Decan-Konnect/VxPlayer`. If the repository is renamed or hosted elsewhere, update the repository links and the `data-repository` value in `docs/index.html`.

## Known platform constraints

LibVLC's native output volume API documents a 0–200 range. VxPlayer adds up to 3.52 dB of digital preamp gain for the 200–300% portion of its slider and enables the VLC compressor audio filter to reduce peaks. Effective gain depends on available VLC audio-filter plugins and the device; it cannot guarantee clipping-free output for every source or listening setup. Picture-in-picture is an always-on-top compact main window, not a separate video renderer.

## License

MIT. See [LICENSE](LICENSE).
