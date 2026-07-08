"""
FixersView — a browsable inventory of loaded addon fixers.

Surfaces the per-addon patch modules discovered by the fixers framework
(see ``src/fixers/__init__.py``) as a readable list with each fixer's
description, target globs, and module name. Read-only — it documents what
runs automatically during the merge pipeline.
"""
import importlib

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QFrame
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from src.core.i18n import _tr


def _collect_fixers():
    """Return a list of dicts {name, description, targets} for every loaded fixer."""
    try:
        from src import fixers as fixers_pkg
        loaded = fixers_pkg.load_fixers()
    except Exception:
        loaded = []
    items = []
    for mod in loaded:
        name = getattr(mod, "__name__", "fixer").split(".")[-1]
        desc = getattr(mod, "DESCRIPTION", "") or ""
        targets = getattr(mod, "TARGETS", []) or []
        items.append({"name": name, "description": desc, "targets": list(targets)})
    return items


class FixersView(QWidget):
    """
    Read-only browser of the loaded addon fixers.
    """

    def __init__(self, parent=None, compact: bool = False):
        """*compact* hides the large heading/subheading — use when embedded
        inside another view (e.g. the Help tab) where the host already
        provides context."""
        super().__init__(parent)
        self._compact = compact
        self._fixers = _collect_fixers()
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

        self._summary = QLabel()
        self._summary.setStyleSheet("color: #C6C6C6; font-weight: 600;")
        layout.addWidget(self._summary)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(3)
        self._tree.setRootIsDecorated(False)
        self._tree.setUniformRowHeights(True)
        self._tree.setAlternatingRowColors(False)
        self._tree.setStyleSheet(
            "QTreeWidget { background-color: #252525; color: #C6C6C6; "
            "border: 3px solid #3D3D3D; } "
            "QTreeWidget::item { padding: 8px; } "
            "QTreeWidget::item:selected { background-color: #7CBD4D; color: #FFFFFF; } "
            "QHeaderView::section { background-color: #3D3D3D; color: #C6C6C6; "
            "border: none; padding: 6px; font-weight: 600; }"
        )
        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self._tree, 1)

    def refresh(self):
        """Reload the fixer list (useful after settings/plugin changes)."""
        self._fixers = _collect_fixers()
        self.retranslate_ui()

    # ── i18n ──────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._heading.setText(_tr("fixers.heading", "Addon Fixers"))
        self._subheading.setText(_tr("fixers.subheading",
            "Patches applied automatically during the merge to upgrade outdated "
            "addon content. These run as part of the pipeline — nothing here needs "
            "to be toggled manually."))
        # When embedded in another view, hide the redundant heading/subheading.
        self._heading.setVisible(not self._compact)
        self._subheading.setVisible(not self._compact)
        n = len(self._fixers)
        self._summary.setText(
            _tr("fixers.summary", "{n} fixer(s) loaded").format(n=n))

        self._tree.setHeaderLabels([
            _tr("fixers.col.description", "Description"),
            _tr("fixers.col.module", "Module"),
            _tr("fixers.col.targets", "Targets"),
        ])

        self._tree.clear()
        for f in self._fixers:
            row = QTreeWidgetItem([
                f["description"] or f["name"],
                f["name"],
                ", ".join(f["targets"]) or "*",
            ])
            row.setForeground(1, QColor("#5CE3E6"))
            row.setForeground(2, QColor("#888888"))
            self._tree.addTopLevelItem(row)
