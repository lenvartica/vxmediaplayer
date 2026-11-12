"""VxPlayer application entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app_version import APP_VERSION
from engine.player import create_vlc_instance
from ui.main_window import MainWindow


def main() -> int:
    if "--check-libvlc" in sys.argv:
        instance = create_vlc_instance()
        if instance is None:
            raise RuntimeError("LibVLC initialization smoke test failed.")
        instance.release()
        return 0

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("VxPlayer")
    app.setOrganizationName("Decan Konnect")
    app.setApplicationVersion(APP_VERSION)
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    stylesheet = bundle_dir / "assets" / "style.qss"
    if not stylesheet.is_file():
        stylesheet = Path(__file__).resolve().parent / "assets" / "style.qss"
    if stylesheet.exists():
        app.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    media_paths = [
        Path(argument).expanduser()
        for argument in sys.argv[1:]
        if not argument.startswith("-") and Path(argument).is_file()
    ]
    if media_paths:
        window.play_path(str(media_paths[0]))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
