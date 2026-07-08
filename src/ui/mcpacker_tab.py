"""
MCPacker tab — a utility for bundling folders into .mcpack format.
Supports both single-pack and directory-of-packs modes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget,
    QPushButton, QLineEdit, QLabel, QComboBox
)
from PySide6.QtCore import Qt, Signal
from src.ui.drop_widgets import DropLineEdit
from src.core.i18n import _tr


class MCPackerTab(QWidget):
    """
    Tab for packing folders into .mcpack format.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Controls group ───────────────────────────────────────────
        self._controls_group = QGroupBox("")
        controls_layout = QVBoxLayout(self._controls_group)

        # Mode selection
        mode_row = QHBoxLayout()
        self._mode_label = QLabel()
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("", "pack")
        self._mode_combo.addItem("", "unpack")
        mode_row.addWidget(self._mode_label)
        mode_row.addWidget(self._mode_combo, 1)
        controls_layout.addLayout(mode_row)

        layout.addWidget(self._controls_group)

        # ── Files group ──────────────────────────────────────────────
        self._files_group = QGroupBox("")
        files_layout = QVBoxLayout(self._files_group)

        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(200)
        files_layout.addWidget(self._file_list)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton()
        self._btn_remove = QPushButton()
        self._btn_remove.setProperty("class", "danger")
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        btn_row.addStretch()
        files_layout.addLayout(btn_row)

        layout.addWidget(self._files_group)

        # ── Output group ─────────────────────────────────────────────
        self._output_group = QGroupBox("")
        output_layout = QHBoxLayout(self._output_group)

        self._out_label = QLabel()
        self._output_path = DropLineEdit()
        self._output_path.setPlaceholderText("")
        self._btn_browse = QPushButton()

        output_layout.addWidget(self._out_label)
        output_layout.addWidget(self._output_path, 1)
        output_layout.addWidget(self._btn_browse)

        layout.addWidget(self._output_group)

        # ── Action buttons ───────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.addStretch()
        self._btn_start = QPushButton()
        self._btn_start.setProperty("class", "primary")
        action_row.addWidget(self._btn_start)
        layout.addLayout(action_row)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #5CE3E6; font-weight: 600;")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.hide()
        layout.addWidget(self._status_label)

        layout.addStretch()

    def retranslate_ui(self):
        self._controls_group.setTitle(_tr("mcpacker.group.controls", "Controls"))
        self._mode_label.setText(_tr("common.mode", "Mode:"))
        self._mode_combo.setItemText(0, _tr("mcpacker.mode.pack", "Pack"))
        self._mode_combo.setItemText(1, _tr("mcpacker.mode.unpack", "Unpack"))
        self._files_group.setTitle(_tr("mcpacker.group.files", "Files / Folders"))
        self._btn_add.setText(_tr("mcpacker.add_folder", "Add Folder"))
        self._btn_remove.setText(_tr("merger.remove_selected", "Remove Selected"))
        self._output_group.setTitle(_tr("merger.group.output", "Output"))
        self._out_label.setText(_tr("mcpacker.output", "Output:"))
        self._output_path.setPlaceholderText(_tr("mcpacker.output_ph", "Output directory..."))
        self._btn_browse.setText(_tr("common.browse", "Browse..."))
        self._btn_start.setText(_tr("common.start", "Start"))

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def mode_combo(self):
        return self._mode_combo

    @property
    def file_list(self):
        return self._file_list

    @property
    def btn_add(self):
        return self._btn_add

    @property
    def btn_remove(self):
        return self._btn_remove

    @property
    def btn_start(self):
        return self._btn_start

    @property
    def output_path(self):
        return self._output_path

    @property
    def btn_browse(self):
        return self._btn_browse

    @property
    def status_label(self):
        return self._status_label

    def set_status(self, text):
        self._status_label.setText(text)
        self._status_label.show()

    def clear_status(self):
        self._status_label.hide()
