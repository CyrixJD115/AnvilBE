"""
Custom widgets for Anvil-MC.
Includes themed status indicators and reusable UI components.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame, QListWidget, QApplication, QStyle
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon
from src.core.i18n import _tr


def style_icon(pixmap: QStyle.StandardPixmap, size: int = 16) -> QIcon:
    """Return a built-in Qt standard icon (no emoji/glyph fallback).

    Uses the application style's :meth:`QStyle.standardIcon` so icons match
    the current platform/theme. Returns an empty icon if unavailable.
    """
    app = QApplication.instance()
    if app is None:
        return QIcon()
    return app.style().standardIcon(pixmap)


class AchievementIndicator(QWidget):
    """
    Custom widget showing green checkmark or red X for achievement compatibility
    status during pack merges.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self._label = QLabel()
        self._label.setStyleSheet("color: #C6C6C6; font-weight: 600;")
        self._layout.addWidget(self._label)

        self._status_icon = QLabel()
        self._status_icon.setFixedSize(18, 18)
        self._status_icon.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._status_icon)

        self._status_text = QLabel()
        self._status_text.setStyleSheet("color: #FFFF55;")
        self._layout.addWidget(self._status_text)

        self._layout.addStretch()

        self._state = "unknown"
        self.retranslate_ui()
        self.set_status_unknown()

    def retranslate_ui(self):
        self._label.setText(_tr("achievements.label", "Achievements:"))
        getattr(self, f"set_status_{self._state}", self.set_status_unknown)()

    def set_status_unknown(self):
        """Set status to unknown/loading."""
        self._state = "unknown"
        self._status_icon.setPixmap(
            style_icon(QStyle.SP_MessageBoxQuestion).pixmap(16, 16))
        self._status_text.setText(_tr("achievements.checking", "Checking..."))
        self._status_text.setStyleSheet("color: #FFFF55;")

    def set_status_compatible(self):
        """Set status to achievement-compatible."""
        self._state = "compatible"
        self._status_icon.setPixmap(
            style_icon(QStyle.SP_DialogApplyButton).pixmap(16, 16))
        self._status_text.setText(_tr("achievements.compatible", "Compatible"))
        self._status_text.setStyleSheet("color: #55FF55;")

    def set_status_incompatible(self):
        """Set status to achievement-incompatible."""
        self._state = "incompatible"
        self._status_icon.setPixmap(
            style_icon(QStyle.SP_MessageBoxCritical).pixmap(16, 16))
        self._status_text.setText(_tr("achievements.incompatible", "Incompatible"))
        self._status_text.setStyleSheet("color: #FF5555;")

    def set_status(self, compatible: bool):
        """Set status from boolean."""
        if compatible:
            self.set_status_compatible()
        else:
            self.set_status_incompatible()


class ThemedSeparator(QFrame):
    """A horizontal line separator with the blocky theme style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("color: #3D3D3D; margin: 4px 0px;")


class StatusLabel(QLabel):
    """A styled status label with the Minecraft theme colors."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "status-mode")
        self.setStyleSheet("color: #5CE3E6; font-weight: 600;")


class DropFileList(QListWidget):
    """A QListWidget that accepts file/folder drag-and-drop."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                paths.append(path)
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()
