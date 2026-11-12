# VxPlayer

**A modern desktop media player by Decan Konnect.** VxPlayer combines a PyQt6 interface with LibVLC playback for a broad range of audio and video formats.

[![Build and release](https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml/badge.svg)](https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml)
[![Deploy GitHub Pages](https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml/badge.svg)](https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

- LibVLC playback for MP4, MKV, AVI, MOV, WMV, FLV, WebM, 3GP, MP3, WAV, FLAC, AAC, OGG, M4A, and additional VLC-supported formats. Files play directly without conversion.
- Hardware decoding is requested from LibVLC when available. 4K, 8K, and HDR playback depends on the source codec, VLC build, GPU, drivers, and display; it cannot be guaranteed by the application.
- Clean white-and-orange PyQt6 interface, normalized seeking, playback queue, filtering, drag-and-drop, M3U8 playlists, and recent-file history.
- Volume slider from 0–300%, using LibVLC volume up to 200% and equalizer preamp gain above that. A compressor filter is enabled to reduce peaks; device and plugin limits still apply. High volume can damage hearing.
- Native 10-band equalizer with Bass Boost, Vocal, Party, Flat, Rock, and Pop curves.
- Playback speed from 0.25x to 4x; pitch preservation depends on LibVLC's `scaletempo` plugin.
- Frame stepping, frame capture, repeat-one/repeat-playlist, A-B repeat, and saved resume positions.
- Audio/video/subtitle track selection, adjacent and external subtitles, subtitle style, and independent audio/subtitle delay adjustment.
- Video zoom, aspect ratio, crop, rotation, brightness, contrast, saturation, gamma, and deinterlacing controls.
- Always-on-top mode, compact picture-in-picture, stereo/channel output choices, configurable keyboard shortcuts, system-tray controls, and Windows media-key integration.
- No analytics or telemetry in the application.
- Windows can check GitHub Releases for a newer build from **Help → Check for updates...**. After the one-time move to the modular package, the updater downloads and verifies only changed application files, applies them after VxPlayer closes, then restarts the player. Older single-EXE installs use the full setup once to migrate.

## Quick start

Python 3.11 or newer and a LibVLC runtime are required. The Windows release workflow bundles LibVLC. Linux builds use system LibVLC.

### Windows installer

Download and run `VxPlayer-Setup.exe` from the [latest release](https://github.com/lenvartica/vxmediaplayer/releases/latest). This small bootstrap downloads and verifies the full installer, then opens the normal setup wizard so you can choose the destination and Windows integration options. The full installer installs the player, LibVLC, Python/Qt runtime, and update helper together so all modules are ready at launch. Windows may ask for administrator approval. The full installer and portable ZIP are also available on the release page.

```powershell
python -m pip install -r requirements.txt
python src/main.py
```

On Linux, install your distribution's VLC/LibVLC packages before launching. If the player reports that LibVLC cannot initialize, verify that the VLC libraries and plugin directory are installed and discoverable. For source runs, install VLC for your operating system.

## Controls

- **Open media** or `Ctrl+O`: choose files; drag files onto the player to add or play them.
- Click the center of the video to play or pause; click the left or right edge to seek back or forward by 10 seconds.
- **Space**: play or pause; **Left / Right**: seek 10 seconds; **Ctrl+Left / Ctrl+Right**: previous / next queue item.
- **M**: mute / restore volume; **F**: fullscreen; **Esc**: leave fullscreen; **S**: stop.
- Double-click an item in the queue to play it. Queue items can be reordered, filtered, removed, and saved as `.m3u8`.
- Playback menu includes frame stepping, speed changes, A-B repeat, repeat-current, and repeat-playlist.
- Video menu includes capture, always-on-top, and video adjustments; Audio and Subtitles menus expose track selection.
- Settings provides audio output, audio/subtitle synchronization, subtitle appearance, and configurable keyboard shortcuts. Windows options also include global hotkeys/media keys, minimize-to-tray, start-at-sign-in, and keeping the display awake during playback.
- Select **Help → Check for updates...** to check stable releases and the rolling Continuous prerelease. Updates are never installed without confirmation. Modular installs fetch only the changed file shards and verify the downloads before replacing installed files.
- `VxPlayer-Setup.exe` is a small online bootstrap for a first install or a one-time migration from the old single-EXE package. It downloads and verifies `VxPlayer-Setup-Full.exe` from the matching GitHub release, then runs the full setup. An internet connection is required. The full ZIP contains all application modules for manual or portable installation.

## Project layout

```text
.github/workflows/  Windows/Linux build, installer, and GitHub Pages deployment
installer/          Inno Setup system installer definition
src/assets/         Flat orange-and-white app mark and light QSS theme
src/engine/         LibVLC wrapper and equalizer
src/ui/             Player, queue, settings, and Windows desktop integration
docs/               GitHub Pages product site
requirements.txt    Pinned Python runtime/build dependencies
```

## Builds and deployment

Every push to `main` builds Windows x64 and Linux x64 artifacts, then refreshes the **VxPlayer Continuous Build** prerelease with the successful outputs. Push a `v*` tag to publish a stable versioned release instead. Both releases include the small online Windows installer, update manifest, portable executable and ZIP, plus the Linux executable and `.tar.gz` package. The installer downloads the matching Windows ZIP and verifies its SHA-256 before extraction. Windows packages the VLC runtime into the PyInstaller executable. Linux output is a PyInstaller executable and requires compatible system LibVLC libraries/plugins.

Before the Pages workflow can deploy, open **Settings → Pages** for the repository and set **Build and deployment → Source** to **GitHub Actions**. The first deployment fails if Pages has not been enabled this way. After enabling it, run **Deploy GitHub Pages** from the Actions tab; later `docs/` changes deploy automatically.

The landing page and badges point to `lenvartica/vxmediaplayer`. Update those links and the `data-repository` value in `docs/index.html` if the repository is renamed or moved.

## Known platform constraints

LibVLC's native output volume API documents a 0–200 range. VxPlayer adds up to 3.52 dB of digital preamp gain for the 200–300% portion of its slider and enables the VLC compressor audio filter to reduce peaks. Effective gain depends on available VLC audio-filter plugins and the device; it cannot guarantee clipping-free output for every source or listening setup. VLC supplies a 10-band native equalizer; gapless playback, crossfade, dedicated spatial-audio processing, and a separate audio visualizer are not currently implemented. Picture-in-picture is an always-on-top compact main window, not a separate video renderer.

## License

MIT. See [LICENSE](LICENSE).
