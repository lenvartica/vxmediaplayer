"""Reorderable media queue."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.player import SUBTITLE_SUFFIXES


class _QueueListWidget(QListWidget):
    files_dropped = pyqtSignal(list)

    def dragEnterEvent(self, event: object) -> None:
        if event.mimeData().hasUrls():  # type: ignore[attr-defined]
            event.acceptProposedAction()  # type: ignore[attr-defined]
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: object) -> None:
        if event.mimeData().hasUrls():  # type: ignore[attr-defined]
            event.acceptProposedAction()  # type: ignore[attr-defined]
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: object) -> None:
        if event.mimeData().hasUrls():  # type: ignore[attr-defined]
            paths = [
                url.toLocalFile()
                for url in event.mimeData().urls()  # type: ignore[attr-defined]
                if url.isLocalFile()
            ]
            event.acceptProposedAction()  # type: ignore[attr-defined]
            self.files_dropped.emit(paths)
            return
        super().dropEvent(event)


class PlaylistWidget(QWidget):
    play_requested = pyqtSignal(str)
    files_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("playlistPanel")
        self.list_widget = _QueueListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.itemDoubleClicked.connect(self._play_item)
        self.list_widget.files_dropped.connect(self._handle_dropped_paths)
        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        self.clear_button = QPushButton("Clear")
        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
        buttons.addWidget(self.clear_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(buttons)
        self.setAcceptDrops(True)
        self.list_widget.setAcceptDrops(True)

    def add_paths(self, paths: list[str | Path]) -> None:
        existing = {
            self.list_widget.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.list_widget.count())
        }
        for item in paths:
            path = Path(item).expanduser().resolve()
            if path.suffix.lower() in SUBTITLE_SUFFIXES or not path.is_file():
                continue
            value = str(path)
            if value in existing:
                continue
            entry = QListWidgetItem(path.name)
            entry.setToolTip(value)
            entry.setData(Qt.ItemDataRole.UserRole, value)
            self.list_widget.addItem(entry)
            existing.add(value)

    def paths(self) -> list[str]:
        return [
            self.list_widget.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.list_widget.count())
        ]

    def set_paths(self, paths: list[str]) -> None:
        self.list_widget.clear()
        self.add_paths(paths)

    def current_path(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def select_path(self, path: str) -> None:
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.list_widget.setCurrentItem(item)
                return

    def _play_item(self, item: QListWidgetItem) -> None:
        self.play_requested.emit(item.data(Qt.ItemDataRole.UserRole))

    def _paths_from_event(self, event: object) -> list[str]:
        urls = event.mimeData().urls()  # type: ignore[attr-defined]
        return [url.toLocalFile() for url in urls if url.isLocalFile()]

    def _handle_dropped_paths(self, paths: list[str]) -> None:
        self.add_paths(paths)
        if paths:
            self.files_dropped.emit(paths)

    def dragEnterEvent(self, event: object) -> None:
        if event.mimeData().hasUrls():  # type: ignore[attr-defined]
            event.acceptProposedAction()  # type: ignore[attr-defined]
        else:
            event.ignore()  # type: ignore[attr-defined]

    def dropEvent(self, event: object) -> None:
        paths = self._paths_from_event(event)
        if paths:
            self._handle_dropped_paths(paths)
            event.acceptProposedAction()  # type: ignore[attr-defined]
        else:
            event.ignore()  # type: ignore[attr-defined]
