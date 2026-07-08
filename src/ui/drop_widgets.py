"""
Drag-and-drop widgets for Anvil-MC.
Provides path inputs and drop zones with green-highlight visual feedback
when a pack file or folder is dragged over them.
"""
import os

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent

from src.core.i18n import _tr


# Extensions accepted everywhere a pack can be dropped.
_PACK_EXTENSIONS = ('.mcpack', '.mcaddon', '.zip')


def _looks_like_pack(path: str) -> bool:
    """Return True if *path* is a pack file or any directory."""
    if not path:
        return False
    if os.path.isdir(path):
        return True
    return path.lower().endswith(_PACK_EXTENSIONS)


class DropLineEdit(QLineEdit):
    """A path input line-edit that accepts .mcpack/.mcaddon/.zip files or
    folders via drag-and-drop, with green-highlight feedback on hover.

    Emits :pyattr:`paths_dropped(list)` for each accepted drop.
    """

    paths_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._set_active(False)

    # ── Drag state ────────────────────────────────────────────────────
    def _set_active(self, active: bool):
        self.setProperty("drag-active", "true" if active else "false")
        # Re-polish so the QSS pseudo-state applies immediately.
        self.style().unpolish(self)
        self.style().polish(self)

    # ── Drag events ───────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and any(
            _looks_like_pack(u.toLocalFile()) for u in event.mimeData().urls()
        ):
            self._set_active(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._set_active(False)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        paths = [p for p in paths if _looks_like_pack(p)]
        self._set_active(False)
        if paths:
            # Single-path inputs get the text set; multi-path drops are signalled
            # so the host can decide (append to a list, etc.).
            if len(paths) == 1:
                self.setText(paths[0])
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


class LabeledDropEdit(QWidget):
    """A label + :class:`DropLineEdit` combo for path inputs.

    Exposes :pyattr:`edit` (the line-edit) and :pyattr:`label` so the host
    can retranslate them.  The line-edit keeps all the line-edit accessors
    (``text()``, ``setText()``, ``setPlaceholderText()``).
    """

    paths_dropped = Signal(list)

    def __init__(self, label_text: str = "", placeholder: str = "", parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        row.addWidget(self.label)

        self.edit = DropLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.paths_dropped.connect(self.paths_dropped)
        row.addWidget(self.edit, 1)
