"""
Console tab — live log output panel.
Captures all Python logging output from every module (merge pipeline, fixers,
pack utils, etc.) and displays it in a read-only text widget with color-coded
log levels.  Thread-safe via a Qt signal bridge so logs from background worker
threads are delivered safely to the GUI thread.
"""
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QApplication
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor
from src.core.i18n import _tr


# ── Log level colors (Minecraft palette) ────────────────────────────────
_LEVEL_COLORS = {
    logging.DEBUG:    "#888888",
    logging.INFO:     "#C6C6C6",
    logging.WARNING:  "#FFAA00",
    logging.ERROR:    "#FF5555",
    logging.CRITICAL: "#FF0000",
}

_LEVEL_PREFIX = {
    logging.DEBUG:    "DBG",
    logging.INFO:     "INF",
    logging.WARNING:  "WRN",
    logging.ERROR:    "ERR",
    logging.CRITICAL: "CRT",
}


class LogSignalBridge(QObject):
    """Thread-safe bridge: logging handler emits signal, GUI thread receives."""
    log_message = Signal(str, int)


class QtLogHandler(logging.Handler):
    """
    A logging.Handler that forwards records to a Qt signal.
    Safe to use from any thread (Qt signals are queued across threads).
    """

    def __init__(self, bridge: LogSignalBridge):
        super().__init__()
        self._bridge = bridge

    def emit(self, record):
        try:
            msg = self.format(record)
            self._bridge.log_message.emit(msg, record.levelno)
        except Exception:
            self.handleError(record)


class ConsoleTab(QWidget):
    """
    Read-only console showing all application log output.
    Includes level filter dropdown and clear/copy buttons.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_level = logging.INFO
        self._setup_ui()
        self.retranslate_ui()

        # ── Wire logging ─────────────────────────────────────────────
        self._bridge = LogSignalBridge()
        self._bridge.log_message.connect(self._append_log)

        self._handler = QtLogHandler(self._bridge)
        self._handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        ))

        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)
        # Ensure we capture everything
        if root_logger.level > logging.DEBUG:
            root_logger.setLevel(logging.INFO)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Toolbar ──────────────────────────────────────────────────
        toolbar = QHBoxLayout()

        level_label = QLabel()
        level_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        toolbar.addWidget(level_label)
        self._level_label = level_label

        self._level_combo = QComboBox()
        self._level_combo.addItem("DEBUG", logging.DEBUG)
        self._level_combo.addItem("INFO", logging.INFO)
        self._level_combo.addItem("WARNING", logging.WARNING)
        self._level_combo.addItem("ERROR", logging.ERROR)
        self._level_combo.setCurrentIndex(1)  # INFO
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        toolbar.addWidget(self._level_combo)

        toolbar.addStretch()

        self._btn_copy = QPushButton()
        self._btn_copy.clicked.connect(self._copy_all)
        toolbar.addWidget(self._btn_copy)

        self._btn_clear = QPushButton()
        self._btn_clear.setProperty("class", "danger")
        self._btn_clear.clicked.connect(self._clear_log)
        toolbar.addWidget(self._btn_clear)

        layout.addLayout(toolbar)

        # ── Log viewer ───────────────────────────────────────────────
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setMinimumHeight(400)
        # Minecraft-style dark terminal
        self._text.setStyleSheet(
            "QTextEdit {"
            "  background-color: #1A1A1A;"
            "  color: #C6C6C6;"
            "  font-family: 'Consolas', 'DejaVu Sans Mono', monospace;"
            "  font-size: 10pt;"
            "  border: 2px solid #3D3D3D;"
            "}"
        )
        layout.addWidget(self._text)

    # ── Slots ─────────────────────────────────────────────────────────

    def retranslate_ui(self):
        self._level_label.setText(_tr("console.log_level", "Log Level:"))
        self._btn_copy.setText(_tr("console.copy_all", "Copy All"))
        self._btn_clear.setText(_tr("common.clear", "Clear"))

    def _append_log(self, message: str, level: int):
        """Append a log line with color based on level (runs in GUI thread)."""
        if level < self._min_level:
            return
        color = _LEVEL_COLORS.get(level, "#C6C6C6")
        prefix = _LEVEL_PREFIX.get(level, "???")
        # HTML-escape the message content
        safe = (message.replace("&", "&amp;")
                       .replace("<", "&lt;")
                       .replace(">", "&gt;"))
        self._text.append(f'<span style="color:{color}"><b>[{prefix}]</b> {safe}</span>')
        self._text.moveCursor(QTextCursor.End)

    def _on_level_changed(self):
        data = self._level_combo.currentData()
        self._min_level = data if data is not None else logging.INFO

    def _clear_log(self):
        self._text.clear()

    def _copy_all(self):
        text = self._text.toPlainText()
        QApplication.instance().clipboard().setText(text)
