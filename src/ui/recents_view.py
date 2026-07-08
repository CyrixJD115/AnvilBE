"""
RecentsView — a history of recently-merged source lists.

Reads the persisted merge history (a rolling log of recent source sets +
output dirs) from the application's settings cache and lets the user
re-load any past set back onto the dashboard with a single click.
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from src.core.i18n import _tr


class RecentsView(QWidget):
    """
    Browsable history of recent merge sessions.

    Emits :pyattr:`restore_requested(list)` with a list of source paths when
    the user clicks "Restore" on an entry. The host loads them onto the
    dashboard.
    """

    restore_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []  # list of {"sources": [...], "output": str}
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._heading = QLabel()
        self._heading.setStyleSheet("color: #7CBD4D; font-size: 18pt; font-weight: 800;")
        layout.addWidget(self._heading)

        self._subheading = QLabel()
        self._subheading.setStyleSheet("color: #888888; font-size: 10pt;")
        self._subheading.setWordWrap(True)
        layout.addWidget(self._subheading)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { background-color: #252525; color: #C6C6C6; "
            "border: 3px solid #3D3D3D; } "
            "QListWidget::item { padding: 10px; } "
            "QListWidget::item:selected { background-color: #7CBD4D; color: #FFFFFF; }")
        self._list.setMinimumHeight(260)
        layout.addWidget(self._list, 1)

        self._empty_hint = QLabel()
        self._empty_hint.setStyleSheet("color: #4D4D4D; font-style: italic;")
        self._empty_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._empty_hint)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_clear = QPushButton()
        self._btn_clear.setProperty("class", "danger")
        self._btn_clear.setCursor(Qt.PointingHandCursor)
        self._btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(self._btn_clear)
        layout.addLayout(btn_row)

    # ── Public API ────────────────────────────────────────────────────
    def load_history(self, history):
        """Populate from a list of {"sources": [...], "output": str} dicts."""
        self._history = list(history or [])
        self._rebuild()

    def get_history(self):
        """Return the current history list (for the host to persist)."""
        return list(self._history)

    def add_entry(self, sources, output=""):
        """Record a new merge session entry at the top (deduped)."""
        sources = [p for p in (sources or []) if p]
        if not sources:
            return
        entry = {"sources": sources, "output": output or ""}
        # Deduplicate by exact source-set fingerprint.
        key = tuple(sorted(sources))
        self._history = [e for e in self._history
                         if tuple(sorted(e.get("sources", []))) != key]
        self._history.insert(0, entry)
        # Keep a rolling window of 12 sessions.
        self._history = self._history[:12]
        self._rebuild()

    # ── Slots ─────────────────────────────────────────────────────────
    def _on_clear(self):
        self._history = []
        self._rebuild()

    def _on_restore(self, item):
        idx = self._list.row(item)
        if 0 <= idx < len(self._history):
            self.restore_requested.emit(list(self._history[idx].get("sources", [])))

    # ── Rendering ─────────────────────────────────────────────────────
    def _rebuild(self):
        self._list.clear()
        if not self._history:
            self._empty_hint.show()
            self._btn_clear.setEnabled(False)
            return
        self._empty_hint.hide()
        self._btn_clear.setEnabled(True)

        for entry in self._history:
            sources = entry.get("sources", [])
            output = entry.get("output", "")
            n = len(sources)
            label = _tr("recents.entry",
                        "{n} pack(s) → {output}").format(
                n=n, output=output or _tr("recents.no_output", "(no output)"))
            if sources:
                preview = sources[0]
                if n > 1:
                    preview += f"  (+{n - 1})"
                label += f"\n     {preview}"
            item = QListWidgetItem(label)
            item.setToolTip("\n".join(sources))
            self._list.addItem(item)
        self._list.itemDoubleClicked.connect(self._on_restore)

    # ── i18n ──────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._heading.setText(_tr("recents.heading", "Recent Merges"))
        self._subheading.setText(_tr("recents.subheading",
            "Your recent merge sessions. Double-click an entry to restore its "
            "pack list onto the dashboard."))
        self._btn_clear.setText(_tr("recents.clear_history", "Clear History"))
        self._empty_hint.setText(_tr("recents.empty",
            "No recent merges yet. Run the pipeline once to see history here."))
        self._rebuild()
