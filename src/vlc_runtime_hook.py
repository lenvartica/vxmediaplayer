"""Make the bundled LibVLC DLLs and plugins discoverable in frozen Windows builds."""

from __future__ import annotations

import os
import sys

if getattr(sys, "frozen", False) and os.name == "nt":
    bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    app_dir = os.path.dirname(sys.executable)
    vlc_dir = os.path.join(app_dir, "vlc")
    if not os.path.isdir(vlc_dir):
        vlc_dir = os.path.join(bundle_dir, "vlc")
    if not os.path.isdir(vlc_dir):
        vlc_dir = bundle_dir
    libvlc_path = os.path.join(vlc_dir, "libvlc.dll")
    if not os.path.isfile(libvlc_path):
        raise FileNotFoundError(f"Bundled LibVLC was not found: {libvlc_path}")
    plugins_dir = os.path.join(vlc_dir, "plugins")
    os.environ["PATH"] = vlc_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ["VLC_PLUGIN_PATH"] = plugins_dir
    os.environ["PYTHON_VLC_MODULE_PATH"] = vlc_dir
    os.environ["PYTHON_VLC_LIB_PATH"] = libvlc_path
    if hasattr(os, "add_dll_directory"):
        _dll_directory_cookie = os.add_dll_directory(vlc_dir)
