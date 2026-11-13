# 🟠 VxPlayer

<h3 align="center">⚡ PLAY BEYOND LIMITS. EXPERIENCE MEDIA DIFFERENTLY.</h3>

<p align="center">
  <img src="https://img.shields.io/badge/DECAN_KONNECT-FF5A1F?style=for-the-badge&logoColor=white" alt="DECAN KONNECT">
  <img src="https://img.shields.io/badge/VxPlayer-MULTIMEDIA-8B5CF6?style=for-the-badge" alt="VxPlayer">
  <img src="https://img.shields.io/badge/DESKTOP-APPLICATION-111827?style=for-the-badge" alt="Desktop Application">
</p>

<p align="center">
  <a href="https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml">
    <img src="https://github.com/lenvartica/vxmediaplayer/actions/workflows/build.yml/badge.svg" alt="Build and release">
  </a>
  <a href="https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml">
    <img src="https://github.com/lenvartica/vxmediaplayer/actions/workflows/pages.yml/badge.svg" alt="Deploy GitHub Pages">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square" alt="MIT License">
  </a>
</p>

<p align="center">
  <i>A new dimension of desktop multimedia.</i>
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/🎵_MUSIC-FF5A1F?style=for-the-badge">
  <img src="https://img.shields.io/badge/🎬_VIDEO-8B5CF6?style=for-the-badge">
  <img src="https://img.shields.io/badge/🎚️_CONTROL-06B6D4?style=for-the-badge">
  <img src="https://img.shields.io/badge/🚀_PERFORMANCE-16A34A?style=for-the-badge">
</p>

**VxPlayer** is a modern desktop multimedia application developed by **DECAN KONNECT**, combining the flexibility of Python, the power of PyQt6, and the playback capabilities of LibVLC.

Designed for people who want more than basic media playback, VxPlayer brings music, movies, playlists, subtitles, audio customization, and advanced video controls into one unified desktop experience.

From everyday music listening to high-resolution video playback, VxPlayer puts the multimedia experience under your control.

<p align="center">
  <a href="https://github.com/lenvartica/vxmediaplayer/releases/latest">
    <img src="https://img.shields.io/badge/⬇_DOWNLOAD_VXPLAYER-FF5A1F?style=for-the-badge&logo=windows&logoColor=white" alt="Download VxPlayer">
  </a>
  <a href="https://github.com/lenvartica/vxmediaplayer">
    <img src="https://img.shields.io/badge/⌘_EXPLORE_SOURCE-8B5CF6?style=for-the-badge&logo=github&logoColor=white" alt="Explore source code">
  </a>
</p>

---

## 🌌 THE VXPLAYER EXPERIENCE

<table>
<tr>
<td width="50%" valign="top">

### 🎬 Universal Playback

Play a wide range of audio and video formats through LibVLC without converting your media.

</td>
<td width="50%" valign="top">

### 🎚️ Audio Intelligence

Fine-tune your listening experience with a 10-band equalizer, audio controls, and adjustable volume.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ⚡ Visual Control

Adjust brightness, contrast, saturation, gamma, zoom, rotation, and aspect ratio.

</td>
<td width="50%" valign="top">

### 📂 Smart Media Management

Create playlists, manage playback queues, filter media, and save M3U8 collections.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🖥️ Desktop Integration

Windows media keys, global shortcuts, system tray controls, and compact picture-in-picture.

</td>
<td width="50%" valign="top">

### 🔄 Intelligent Updates

Check GitHub releases, verify updates, and update changed application modules.

</td>
</tr>
</table>

---

## 🚀 FEATURE MATRIX

### 🎥 01 — Advanced Media Engine

Powered by LibVLC, VxPlayer supports a broad collection of media formats.

**Video**

`MP4` `MKV` `AVI` `MOV` `WMV` `FLV` `WebM` `3GP`

**Audio**

`MP3` `WAV` `FLAC` `AAC` `OGG` `M4A`

Additional formats supported by the installed VLC runtime may also work.

### ⚡ 02 — High-Resolution Playback

VxPlayer requests hardware decoding through LibVLC when available.

4K, 8K, and HDR playback depend on the media codec, GPU, graphics drivers, VLC configuration, and display hardware. These capabilities cannot be guaranteed by the application.

### 🎨 03 — Modern Desktop Interface

A clean white-and-orange interface designed for comfortable navigation.

- Organized playback controls.
- Media queue management.
- Search and filtering.
- Drag-and-drop media support.
- Recent media history.
- Normalized playback seeking.
- Configurable keyboard shortcuts.

### 🔊 04 — Advanced Audio System

| Capability | Specification |
|---|---|
| Volume range | 0–300% |
| Native LibVLC volume | Up to 200% |
| Additional amplification | Digital preamp gain |
| Audio processing | Compressor filter support |
| Equalizer | 10-band |
| Output | Stereo and channel options |

The 200–300% range uses additional digital preamp gain. A compressor filter is enabled to help reduce peaks, but distortion-free output cannot be guaranteed.

**⚠️ Hearing safety:** High playback volume can damage hearing.

### 🎛️ 05 — Professional Equalizer

Available presets:

- 🟠 Bass Boost
- 🟣 Vocal
- 🔵 Party
- ⚪ Flat
- 🔴 Rock
- 🟢 Pop

Individual frequency adjustments are supported through the native LibVLC equalizer.

### ⏩ 06 — Playback Speed Control

Take control of playback speed.

| Speed | Usage |
|---|---|
| 0.25x | Very slow |
| 0.5x | Slow |
| 0.75x | Reduced speed |
| 1.0x | Normal |
| 1.25x | Slightly faster |
| 1.5x | Faster |
| 2.0x | Double speed |
| Up to 4.0x | Maximum supported speed |

Pitch preservation depends on LibVLC's `scaletempo` plugin.

### 📃 07 — Playlist Command Centre

- Create and manage playback queues.
- Add multiple media files.
- Reorder queue items.
- Remove individual items.
- Search and filter queue contents.
- Save playlists in M3U8 format.
- Load existing M3U8 playlists.
- Double-click an item to play it.
- Drag and drop files into the player.

### 💬 08 — Subtitle Control

- Audio track selection.
- Video track selection.
- Subtitle track selection.
- External subtitle loading.
- Adjacent subtitle discovery.
- Subtitle appearance customization.
- Independent subtitle delay adjustment.
- Audio and subtitle synchronization.

### 🖥️ 09 — Video Customization

- Video zoom.
- Aspect ratio selection.
- Video cropping.
- Rotation.
- Brightness.
- Contrast.
- Saturation.
- Gamma.
- Deinterlacing.
- Frame capture.
- Frame-by-frame stepping.

### 🪟 10 — Windows Integration

- System tray controls.
- Windows media-key integration.
- Global hotkeys.
- Always-on-top mode.
- Compact picture-in-picture mode.
- Minimize-to-tray functionality.
- Start-at-sign-in option.
- Display-awake support during playback.

Picture-in-picture uses a compact always-on-top main window rather than a separate video renderer.

### 🔁 11 — Advanced Playback

- Repeat current media.
- Repeat entire playlist.
- A-B repeat.
- Saved playback resume positions.
- Frame stepping.
- Playback seeking.
- Fullscreen mode.
- Stop and restart controls.

### 🔄 12 — Modular Update Technology

Access the updater through:

**Help → Check for updates...**

Supported functionality:

- Stable release checks.
- Continuous prerelease checks.
- Update confirmation before installation.
- SHA-256 verification.
- Modular application updates.
- Downloading only changed application files after migration.
- Applying updates after VxPlayer closes.
- Restarting the player after successful updates.

Older single-EXE installations require a one-time migration using the full installer.

### 🔒 13 — Privacy First

VxPlayer does not implement application analytics or telemetry.

No user account is required for local media playback.

---

## 📥 DOWNLOAD & INSTALLATION

<p align="center">
  <a href="https://github.com/lenvartica/vxmediaplayer/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD_LATEST_RELEASE-FF5A1F?style=for-the-badge&logo=github&logoColor=white" alt="Download latest release">
  </a>
</p>

### 🪟 Windows Installation

1. Visit the [VxPlayer Releases](https://github.com/lenvartica/vxmediaplayer/releases/latest) page.
2. Download `VxPlayer-Setup.exe`.
3. Run the bootstrap installer.
4. Allow it to download and verify the corresponding full installer.
5. Follow the Windows setup wizard.
6. Launch VxPlayer.

The full installer includes the application, LibVLC runtime, Python and Qt runtime dependencies, update helper, and required modules.

The release page also provides the full installer and portable ZIP.

### 🐧 Linux Installation

Install VLC and LibVLC:

```bash
sudo apt update
sudo apt install vlc libvlc-dev
```

Download the Linux executable or TAR.GZ archive from the [latest release](https://github.com/lenvartica/vxmediaplayer/releases/latest).

Linux requires compatible system LibVLC libraries and plugins.

### 🧑‍💻 Run from Source

**Requirements**

- Python 3.11+
- LibVLC runtime
- Git
- pip

Clone:

```bash
git clone https://github.com/lenvartica/vxmediaplayer.git
```

Enter the project:

```bash
cd vxmediaplayer
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch:

```bash
python src/main.py
```

---

## ⌨️ KEYBOARD CONTROL SYSTEM

| Shortcut | Action |
|---|---|
| `Ctrl + O` | Open media |
| `Space` | Play / Pause |
| `Left Arrow` | Seek backward 10 seconds |
| `Right Arrow` | Seek forward 10 seconds |
| `Ctrl + Left` | Previous queue item |
| `Ctrl + Right` | Next queue item |
| `M` | Mute / Restore volume |
| `F` | Fullscreen |
| `Esc` | Exit fullscreen |
| `S` | Stop playback |

Additional shortcuts are configurable through Settings.

### 🖱️ Mouse Controls

| Action | Function |
|---|---|
| Click video center | Play / Pause |
| Click video left edge | Seek backward 10 seconds |
| Click video right edge | Seek forward 10 seconds |
| Double-click queue item | Play selected media |
| Drag and drop files | Add or play media |

---

## 🏗️ SYSTEM ARCHITECTURE

VxPlayer uses a modular architecture that separates the playback engine, interface, desktop integration, and build configuration.

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

## ⚙️ AUTOMATED BUILD & RELEASE PIPELINE

VxPlayer uses GitHub Actions to automate its application builds and releases.

### 🔵 Continuous Builds

Every push to `main` triggers the configured build workflow.

The workflow builds:

- Windows x64 artifacts.
- Linux x64 artifacts.

Successful outputs are published to the **VxPlayer Continuous Build** prerelease.

### 🟢 Stable Releases

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

### 🌐 GitHub Pages Deployment

The product website is maintained under `docs/`.

To enable deployment:

1. Open repository Settings.
2. Navigate to Pages.
3. Select **GitHub Actions** as the deployment source.
4. Open Actions.
5. Run the Deploy GitHub Pages workflow.

Subsequent changes to `docs/` deploy automatically.

---

## 🧰 TECHNOLOGY STACK

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white">
  <img src="https://img.shields.io/badge/LibVLC-FF8800?style=for-the-badge">
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">
  <img src="https://img.shields.io/badge/PyInstaller-3776AB?style=for-the-badge">
  <img src="https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white">
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black">
</p>

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

## ⚠️ KNOWN PLATFORM LIMITATIONS

VxPlayer uses LibVLC as its playback engine. Some capabilities depend on the underlying VLC runtime, plugins, operating system, and hardware.

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

## 📜 LICENSE

<p align="center">
  <img src="https://img.shields.io/badge/OPEN_SOURCE-MIT_LICENSE-22C55E?style=for-the-badge&logo=opensourceinitiative&logoColor=white">
</p>

VxPlayer is distributed under the **MIT License**.

See [LICENSE](LICENSE) for the complete license.

---

## 🌐 CONNECT WITH VXPLAYER

| Resource | Link |
|---|---|
| 📦 Latest Release | [Download VxPlayer](https://github.com/lenvartica/vxmediaplayer/releases/latest) |
| 💻 Source Code | [GitHub Repository](https://github.com/lenvartica/vxmediaplayer) |
| ⚙️ Build Pipeline | [GitHub Actions](https://github.com/lenvartica/vxmediaplayer/actions) |
| 🌐 Product Website | [VxPlayer Pages](https://lenvartica.github.io/vxmediaplayer/) |
| 🏢 Developer | [DECAN KONNECT](https://decankonnect.co.ke) |

---

## 🏢 POWERED BY DECAN KONNECT

VxPlayer is a desktop software product developed under **DECAN KONNECT**, founded by **Lenny Muriuki**.

We believe technology should solve real problems, improve everyday experiences, and create opportunities without boundaries.

VxPlayer represents our commitment to building practical software products and useful digital solutions.

<p align="center">
  <img src="https://img.shields.io/badge/DECAN_KONNECT-BUILDING_TECHNOLOGY_FOR_THE_WORLD-FF5A1F?style=for-the-badge" alt="DECAN KONNECT">
</p>

<h2 align="center">🟠 VXPLAYER</h2>

<h3 align="center">PLAY BEYOND LIMITS.</h3>

<p align="center">
  <strong>Music. Movies. Freedom.</strong>
  <br><br>
  Developed with innovation by <strong>DECAN KONNECT</strong>.
  <br>
  <a href="https://decankonnect.co.ke">decankonnect.co.ke</a>
</p>

<p align="center">
  <sub>© 2026 DECAN KONNECT. VxPlayer is an independently developed desktop media player.</sub>
</p>
