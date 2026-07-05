"""
MCPacker tab — a utility for bundling folders into .mcpack format.
Supports both single-pack and directory-of-packs modes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget,
    QPushButton, QLineEdit, QLabel, QComboBox
)
from PySide6.QtCore import Qt


class MCPackerTab(QWidget):
    """
    Tab for packing folders into .mcpack format.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Controls group ───────────────────────────────────────────
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Mode selection
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Pack", "Unpack"])
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self._mode_combo, 1)
        controls_layout.addLayout(mode_row)

        layout.addWidget(controls_group)

        # ── Files group ──────────────────────────────────────────────
        files_group = QGroupBox("Files / Folders")
        files_layout = QVBoxLayout(files_group)

        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(200)
        files_layout.addWidget(self._file_list)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Add Folder")
        self._btn_remove = QPushButton("Remove Selected")
        self._btn_remove.setProperty("class", "danger")
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        btn_row.addStretch()
        files_layout.addLayout(btn_row)

        layout.addWidget(files_group)

        # ── Output group ─────────────────────────────────────────────
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout(output_group)

        out_label = QLabel("Output:")
        self._output_path = QLineEdit()
        self._output_path.setPlaceholderText("Output directory...")
        self._btn_browse = QPushButton("Browse...")

        output_layout.addWidget(out_label)
        output_layout.addWidget(self._output_path, 1)
        output_layout.addWidget(self._btn_browse)

        layout.addWidget(output_group)

        # ── Action buttons ───────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.addStretch()
        self._btn_start = QPushButton("Start")
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
