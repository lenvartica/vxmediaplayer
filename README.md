# 🎬 VxPlayer

### Play Beyond Limits. Experience Media Differently.

**A Modern Desktop Media Player by DECAN KONNECT**

<p align="center">
  <img src="https://img.shields.io/badge/DECAN-KONNECT-EA580C?style=for-the-badge" alt="DECAN KONNECT">
  <img src="https://img.shields.io/badge/VxPlayer-Media%20Player-F97316?style=for-the-badge" alt="VxPlayer">
  <img src="https://img.shields.io/badge/Desktop-Application-222222?style=for-the-badge" alt="Desktop Application">
</p>

<p align="center">
  <a href="https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml">
    <img src="https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml/badge.svg" alt="Build and release">
  </a>
  <a href="https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml">
    <img src="https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml/badge.svg" alt="Deploy GitHub Pages">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  </a>
</p>

---

**One player. Your entire media experience.**

VxPlayer is a modern desktop multimedia application developed by **DECAN KONNECT**, combining the flexibility of Python, the power of PyQt6, and the proven playback capabilities of LibVLC.

Designed for people who want more than basic media playback, VxPlayer brings music, movies, playlists, subtitles, audio customization, and advanced video controls together in one unified desktop experience.

Whether you're enjoying your favourite music, watching high-resolution movies, managing large media collections, or fine-tuning your playback experience, VxPlayer puts you in control.

<p align="center">
  <strong>🎵 Music. 🎬 Movies. 🎚️ Control. 🚀 Performance.</strong>
</p>

## 🌟 Why VxPlayer?

- **Universal media playback:** Play a wide range of audio and video formats without converting files.
- **Powerful playback engine:** Built on LibVLC for extensive codec and media compatibility.
- **Advanced audio experience:** Enjoy a 10-band equalizer, audio effects, and volume controls up to 300%.
- **Complete video control:** Adjust brightness, contrast, saturation, gamma, zoom, crop, and rotation.
- **Smart playlist management:** Organize, filter, reorder, and save your media collections.
- **Subtitle customization:** Manage subtitle tracks, external subtitles, appearance, and synchronization.
- **Desktop integration:** Enjoy Windows media keys, global shortcuts, system tray controls, and compact picture-in-picture.
- **Automatic updates:** Check for new releases directly from the application.
- **Privacy-conscious:** No application analytics or telemetry.

## 🚀 Explore VxPlayer

| Resource | Access |
|---|---|
| 📦 Download VxPlayer | [Latest Releases](https://github.com/lenvartica/vxmediaplayer/releases/latest) |
| 💻 Source Code | [GitHub Repository](https://github.com/lenvartica/vxmediaplayer) |
| ⚙️ Build Status | [GitHub Actions](https://github.com/lenvartica/vxmediaplayer/actions) |
| 🌐 Product Website | [VxPlayer Pages](https://lenvartica.github.io/vxmediaplayer/) |
| 🏢 Developer | [DECAN KONNECT](https://decankonnect.co.ke) |

---

## ✨ Features

### 🎬 1. Extensive Media Format Support

Powered by LibVLC, VxPlayer supports a broad range of audio and video formats without requiring users to convert their media files.

**Video formats:**
- MP4
- MKV
- AVI
- MOV
- WMV
- FLV
- WebM
- 3GP
- Additional VLC-supported formats.

**Audio formats:**
- MP3
- WAV
- FLAC
- AAC
- OGG
- M4A
- Additional VLC-supported formats.

### ⚡ 2. High-Resolution Playback

VxPlayer requests hardware decoding through LibVLC when available.

Playback performance depends on the media codec, GPU, graphics drivers, VLC configuration, and display hardware.

4K, 8K, and HDR playback depend on the capabilities of the underlying system and are not guaranteed by the application.

### 🎨 3. Modern Desktop Interface

A clean white-and-orange interface designed for convenient navigation and media management.

- Organized playback controls.
- Media queue management.
- Search and filtering.
- Drag-and-drop media support.
- Recent media history.
- Normalized playback seeking.
- Configurable keyboard shortcuts.

### 🔊 4. Advanced Audio Controls

- Volume adjustment from 0% to 300%.
- LibVLC native volume control up to 200%.
- Additional digital preamp gain above 200%.
- Compressor filter support to help reduce audio peaks.
- Audio output device selection.
- Stereo and channel output options.
- Independent audio synchronization.

**Note:** High volume can damage hearing. Digital amplification and compression cannot guarantee distortion-free output for every audio source or device.

### 🎚️ 5. Built-in 10-Band Equalizer

Available presets:
- Bass Boost
- Vocal
- Party
- Flat
- Rock
- Pop

Individual frequency adjustments are also supported.

### ⏩ 6. Flexible Playback Speed

Adjust playback speed from 0.25x to 4.0x.

Pitch preservation depends on LibVLC's `scaletempo` plugin.

### 📃 7. Playlist and Queue Management

- Create and manage playback queues.
- Add multiple media files.
- Reorder queue items.
- Remove individual items.
- Search and filter queue contents.
- Save playlists in M3U8 format.
- Load existing M3U8 playlists.
- Double-click an item to start playback.
- Drag and drop files into the player.

### 💬 8. Advanced Subtitle Management

- Audio track selection.
- Video track selection.
- Subtitle track selection.
- External subtitle loading.
- Adjacent subtitle discovery.
- Subtitle appearance customization.
- Independent subtitle delay adjustment.
- Audio and subtitle synchronization controls.

### 🖥️ 9. Advanced Video Controls

- Video zoom.
- Aspect ratio selection.
- Video cropping.
- Rotation.
- Brightness adjustment.
- Contrast adjustment.
- Saturation adjustment.
- Gamma adjustment.
- Deinterlacing.
- Frame capture.
- Frame-by-frame stepping.

### 🪟 10. Windows Desktop Integration

- System tray controls.
- Windows media-key integration.
- Global hotkeys.
- Always-on-top mode.
- Compact picture-in-picture mode.
- Minimize-to-tray functionality.
- Start-at-sign-in option.
- Display-awake support during playback.

Picture-in-picture uses a compact always-on-top main window rather than an independent video renderer.

### 🔁 11. Advanced Playback Management

- Repeat current media.
- Repeat entire playlist.
- A-B repeat.
- Saved playback resume positions.
- Frame stepping.
- Playback seeking.
- Fullscreen mode.
- Stop and restart controls.

### 🔄 12. Automatic Update System

Navigate to **Help → Check for updates...** to check for newer releases.

The updater supports:
- Stable release checks.
- Continuous prerelease checks.
- Update confirmation before installation.
- SHA-256 verification.
- Modular application updates.
- Downloading only changed application files after migration to the modular package.
- Applying updates after the player closes.
- Restarting VxPlayer after successful updates.

Older single-EXE installations require a one-time migration using the full installer.

### 🔒 13. Privacy

VxPlayer does not implement application analytics or telemetry. The application is designed to provide local media playback without requiring a user account.

---

## 📥 Installation

### Windows

Download the latest Windows installer:

**[⬇️ Download VxPlayer for Windows](https://github.com/lenvartica/vxmediaplayer/releases/latest)**

1. Download `VxPlayer-Setup.exe`.
2. Run the bootstrap installer.
3. Allow it to download and verify the corresponding full installer.
4. Follow the Windows setup wizard.
5. Launch VxPlayer.

The full installer includes:
- VxPlayer application files.
- LibVLC runtime.
- Python and Qt runtime dependencies.
- Update helper.
- Required application modules.

The release page also provides the full installer and portable ZIP.

### Linux

Install VLC and LibVLC using your distribution's package manager.

For Ubuntu or Debian:

```bash
sudo apt update
sudo apt install vlc libvlc-dev
```

Download the Linux executable or archive from:

[Latest VxPlayer Releases](https://github.com/lenvartica/vxmediaplayer/releases/latest)

### Running from Source

**Requirements:**
- Python 3.11 or newer.
- LibVLC runtime.
- Git.
- pip.

Clone the repository:

```bash
git clone https://github.com/lenvartica/vxmediaplayer.git
```

Enter the project directory:

```bash
cd vxmediaplayer
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch VxPlayer:

```bash
python src/main.py
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + O` | Open media |
| `Space` | Play / Pause |
| `Left Arrow` | Seek backward 10 seconds |
| `Right Arrow` | Seek forward 10 seconds |
| `Ctrl + Left` | Previous queue item |
| `Ctrl + Right` | Next queue item |
| `M` | Mute / Restore volume |
| `F` | Enter fullscreen |
| `Esc` | Exit fullscreen |
| `S` | Stop playback |

Additional shortcuts can be configured through Settings.

### Mouse Controls

| Action | Function |
|---|---|
| Click video center | Play / Pause |
| Click video left edge | Seek backward 10 seconds |
| Click video right edge | Seek forward 10 seconds |
| Double-click queue item | Play selected media |
| Drag and drop files | Add or play media |

---

## 🏗️ Project Architecture

```text
vxmediaplayer/
│
├── .github/
│   └── workflows/
│       ├── build.yml
│       └── pages.yml
│
├── installer/
│   └── Inno Setup configuration
│
├── src/
│   ├── assets/
│   │   ├── Application graphics
│   │   └── QSS interface theme
│   │
│   ├── engine/
│   │   ├── LibVLC playback wrapper
│   │   └── Audio equalizer
│   │
│   ├── ui/
│   │   ├── Main player interface
│   │   ├── Media queue
│   │   ├── Settings
│   │   └── Windows desktop integration
│   │
│   └── main.py
│
├── docs/
│   └── GitHub Pages product website
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## ⚙️ Build and Release Pipeline

VxPlayer uses GitHub Actions to automate application builds and releases.

### Continuous Builds

Every push to `main` triggers the configured build workflow.

The workflow builds Windows x64 and Linux x64 artifacts.

Successful outputs are published to the **VxPlayer Continuous Build** prerelease.

### Stable Releases

Push a version tag to publish a stable release.

Example:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Release packages include:
- Windows online bootstrap installer.
- Full Windows installer.
- Windows portable executable.
- Windows portable ZIP.
- Update manifest.
- Linux executable.
- Linux TAR.GZ package.

Windows packages the VLC runtime with the PyInstaller executable. Linux builds use system LibVLC libraries and plugins.

### GitHub Pages

The product website is maintained under `docs/`.

To enable deployment:

1. Open repository Settings.
2. Navigate to Pages.
3. Set the deployment source to **GitHub Actions**.
4. Open Actions.
5. Run the Deploy GitHub Pages workflow.

Subsequent changes to `docs/` deploy automatically.

---

## ⚠️ Known Limitations

VxPlayer uses LibVLC as its playback engine. Some capabilities depend on the underlying VLC runtime, plugins, operating system, and hardware.

Current limitations include:

- 4K, 8K, and HDR playback depend on hardware and codec compatibility.
- The volume slider's 200–300% range uses additional digital preamp gain.
- The compressor filter depends on available VLC audio-filter plugins.
- Pitch preservation depends on the `scaletempo` plugin.
- Gapless playback is not currently implemented.
- Crossfade is not currently implemented.
- Dedicated spatial-audio processing is not currently implemented.
- A separate audio visualizer is not currently implemented.
- Picture-in-picture uses the compact main window.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| PyQt6 | Desktop graphical interface |
| LibVLC | Audio and video playback |
| VLC Plugins | Media processing |
| PyInstaller | Application packaging |
| Inno Setup | Windows installation |
| GitHub Actions | Automated builds and releases |
| GitHub Pages | Product website |

---

## 📜 License

VxPlayer is distributed under the **MIT License**.

See [LICENSE](LICENSE) for the complete license.

---

## 🌐 Official Links

- 📦 [Download VxPlayer](https://github.com/lenvartica/vxmediaplayer/releases/latest)
- 💻 [Source Code](https://github.com/lenvartica/vxmediaplayer)
- ⚙️ [Build Actions](https://github.com/lenvartica/vxmediaplayer/actions)
- 🌐 [Product Website](https://lenvartica.github.io/vxmediaplayer/)
- 🏢 [DECAN KONNECT Official Website](https://decankonnect.co.ke)

---

## 🏢 Built by DECAN KONNECT

VxPlayer is a desktop software product developed under **DECAN KONNECT**, founded by **Lenny Muriuki**.

We believe technology should be built to solve real problems, improve everyday experiences, and create opportunities without boundaries.

VxPlayer is part of our commitment to building practical software products and useful digital solutions.

<p align="center">
  <strong>DECAN KONNECT</strong>
  <br>
  Building Technology for the World.
  <br><br>
  <strong>VxPlayer — Play Beyond Limits.</strong>
  <br>
  <a href="https://decankonnect.co.ke">decankonnect.co.ke</a>
</p>
