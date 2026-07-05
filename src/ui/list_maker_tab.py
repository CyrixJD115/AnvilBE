"""
List Maker tab — organizes files by creation date with grouping by Script API version.
Useful for seeing packs organized chronologically.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from src.core.i18n import _tr


class ListMakerTab(QWidget):
    """
    Tab for organizing files by date and version group.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Controls ─────────────────────────────────────────────────
        self._controls_group = QGroupBox("")
        controls_layout = QHBoxLayout(self._controls_group)

        self._btn_add_files = QPushButton()
        self._btn_clear = QPushButton()
        self._btn_clear.setProperty("class", "danger")
        self._btn_organize = QPushButton()
        self._btn_organize.setProperty("class", "primary")
        self._btn_export = QPushButton()
        self._btn_export.setProperty("class", "adco")

        controls_layout.addWidget(self._btn_add_files)
        controls_layout.addWidget(self._btn_clear)
        controls_layout.addStretch()
        controls_layout.addWidget(self._btn_organize)
        controls_layout.addWidget(self._btn_export)

        layout.addWidget(self._controls_group)

        # ── File tree ────────────────────────────────────────────────
        self._tree_group = QGroupBox("")
        tree_layout = QVBoxLayout(self._tree_group)

        self._file_tree = QTreeWidget()
        self._file_tree.setHeaderLabels(["Filename", "Type", "Date Modified"])
        self._file_tree.setAlternatingRowColors(False)
        tree_layout.addWidget(self._file_tree)

        layout.addWidget(self._tree_group)

        # ── Status ───────────────────────────────────────────────────
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #5CE3E6; font-weight: 600;")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.hide()
        layout.addWidget(self._status_label)

    def retranslate_ui(self):
        self._controls_group.setTitle(_tr("list_maker.group.controls", "Controls"))
        self._btn_add_files.setText(_tr("list_maker.add_files", "Add Files"))
        self._btn_clear.setText(_tr("common.clear", "Clear"))
        self._btn_organize.setText(_tr("list_maker.organize_by_date", "Organize by Date"))
        self._btn_export.setText(_tr("list_maker.export_list", "Export List"))
        self._tree_group.setTitle(_tr("list_maker.group.pack_files", "Pack Files"))
        self._file_tree.setHeaderLabels([
            _tr("list_maker.col.filename", "Filename"),
            _tr("common.type", "Type"),
            _tr("list_maker.col.date_modified", "Date Modified"),
        ])

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def btn_add_files(self):
        return self._btn_add_files

    @property
    def btn_clear(self):
        return self._btn_clear

    @property
    def btn_organize(self):
        return self._btn_organize

    @property
    def btn_export(self):
        return self._btn_export

    @property
    def file_tree(self):
        return self._file_tree

    @property
    def status_label(self):
        return self._status_label

    def set_status(self, text):
        self._status_label.setText(text)
        self._status_label.show()

    def clear_status(self):
        self._status_label.hide()

    def clear_tree(self):
        self._file_tree.clear()

    def add_top_level_item(self, item):
        self._file_tree.addTopLevelItem(item)
