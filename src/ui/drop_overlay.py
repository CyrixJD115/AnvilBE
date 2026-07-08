"""
DropOverlay — a window-wide drag-and-drop overlay.

Instead of a dedicated drop box, the entire window accepts drag-and-drop.
When the user drags a pack file/folder anywhere over the window, a
full-surface overlay fades in with a message ("Drop to add packs…"), a
green dashed border, and the list of accepted paths. Dropping (or leaving)
hides the overlay again. Accepted paths are emitted via :pyattr:`paths_dropped`.
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QApplication, QStyle
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent

from src.ui.drop_widgets import _looks_like_pack
from src.core.i18n import _tr


class DropOverlay(QWidget):
    """
    A semi-transparent overlay shown across the whole main window while a
    drag-and-drop carrying pack files is in progress.

    Install on the main window via :meth:`attach`, then the overlay handles
    drag enter/leave/drop on the window and emits :pyattr:`paths_dropped`.
    """

    paths_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.hide()

        # Inner border frame (green dashed) filling the window.
        self._frame = QFrame(self)
        self._frame.setProperty("class", "drop-overlay-frame")

        inner = QVBoxLayout(self._frame)
        inner.setContentsMargins(40, 40, 40, 40)
        inner.setAlignment(Qt.AlignCenter)
        inner.setSpacing(10)

        self._icon = QLabel()
        self._icon.setProperty("class", "drop-overlay-icon")
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFixedSize(72, 72)
        self._set_overlay_icon()
        inner.addWidget(self._icon)

        self._title = QLabel()
        self._title.setProperty("class", "drop-overlay-title")
        self._title.setAlignment(Qt.AlignCenter)
        inner.addWidget(self._title)

        self._subtitle = QLabel()
        self._subtitle.setProperty("class", "drop-overlay-subtitle")
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._subtitle.setWordWrap(True)
        inner.addWidget(self._subtitle)

        # Opacity fade animation
        self._opacity_anim = None
        self._retranslate()
        self._resize_to_parent()

    # ── Public API ────────────────────────────────────────────────────
    def attach(self, window):
        """Install this overlay on *window* and wire its drag events.

        The overlay is parented to the window's central widget so it
        follows resizes and stays above the content.
        """
        self.setParent(window)
        self._window = window
        window.installEventFilter(self)
        self._resize_to_parent()
        self.retranslate_ui()

    def retranslate_ui(self):
        self._retranslate()

    def _set_overlay_icon(self):
        """Render the built-in down-arrow icon into the overlay's icon label."""
        app = QApplication.instance()
        if app is None:
            return
        icon = app.style().standardIcon(QStyle.SP_ArrowDown)
        self._icon.setPixmap(icon.pixmap(64, 64))

    def _retranslate(self):
        self._title.setText(_tr("overlay.title", "Drop to add packs"))
        self._subtitle.setText(_tr("overlay.subtitle",
            ".mcpack  •  .mcaddon  •  .zip  •  raw project folders"))
        self._set_overlay_icon()

    # ── Geometry ──────────────────────────────────────────────────────
    def _resize_to_parent(self):
        parent = self.parent()
        if parent is None:
            return
        rect = parent.rect()
        self.setGeometry(rect)
        if hasattr(self, "_frame"):
            self._frame.setGeometry(self.rect().adjusted(12, 12, -12, -12))
            self._frame.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._frame.setGeometry(self.rect().adjusted(12, 12, -12, -12))

    # ── Event filter on the window ────────────────────────────────────
    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QDragEnterEvent.Type.DragEnter:
            self._on_drag_enter(event)
            return True
        if etype == QDragMoveEvent.Type.DragMove:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            return True
        if etype == QDragLeaveEvent.Type.DragLeave:
            self._hide_overlay()
            return True
        if etype == QDropEvent.Type.Drop:
            self._on_drop(event)
            return True
        if etype == QDragMoveEvent.Type.DragMove:
            return True
        return super().eventFilter(obj, event)

    # ── Drag handling ─────────────────────────────────────────────────
    def _on_drag_enter(self, event: QDragEnterEvent):
        mime = event.mimeData()
        if mime.hasUrls() and any(_looks_like_pack(u.toLocalFile()) for u in mime.urls()):
            event.acceptProposedAction()
            self._show_overlay()
        else:
            event.ignore()

    def _on_drop(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        paths = [p for p in paths if _looks_like_pack(p)]
        self._hide_overlay()
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    # ── Show / hide (fading) ──────────────────────────────────────────
    def _show_overlay(self):
        self._resize_to_parent()
        self.raise_()
        self.show()
        # Simple fade-in via window opacity if possible.
        try:
            if self._opacity_anim is None:
                from PySide6.QtWidgets import QGraphicsOpacityEffect
                self._effect = QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(self._effect)
                self._opacity_anim = QPropertyAnimation(self._effect, b"opacity", self)
                self._opacity_anim.setDuration(120)
                self._opacity_anim.setEasingCurve(QEasingCurve.OutQuad)
            self._opacity_anim.stop()
            self._opacity_anim.setStartValue(self._effect.opacity() or 0.0)
            self._opacity_anim.setEndValue(0.97)
            self._opacity_anim.start()
        except Exception:
            pass

    def _hide_overlay(self):
        try:
            if self._opacity_anim is not None:
                self._opacity_anim.stop()
                self._opacity_anim.setStartValue(self._effect.opacity())
                self._opacity_anim.setEndValue(0.0)
                self._opacity_anim.finished.connect(self.hide)
                self._opacity_anim.start()
                return
        except Exception:
            pass
        self.hide()
