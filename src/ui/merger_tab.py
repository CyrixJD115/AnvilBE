"""
Merger tab — the primary tab for addon pack merging.
Provides file list, controls, progress tracking, and triggers the merge pipeline.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget,
    QPushButton, QLineEdit, QProgressBar, QLabel, QComboBox
)
from PySide6.QtCore import Qt
from src.ui.widgets import AchievementIndicator, DropFileList
from src.core.i18n import _tr


class MergerTab(QWidget):
    """
    Main merger tab with file selection, output configuration, and merge controls.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Files group ──────────────────────────────────────────────
        self._files_group = QGroupBox("")
        files_layout = QVBoxLayout(self._files_group)

        self.file_list_box = DropFileList()
        self.file_list_box.setMinimumHeight(220)
        self.file_list_box.setAlternatingRowColors(False)
        self.file_list_box.setSelectionMode(QListWidget.ExtendedSelection)
        files_layout.addWidget(self.file_list_box)

        layout.addWidget(self._files_group)

        # ── Button row ───────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self._btn_add = QPushButton()
        self._btn_add_folder = QPushButton()
        self._btn_remove = QPushButton()
        self._btn_remove.setProperty("class", "danger")
        self._btn_check_packs = QPushButton()
        self._btn_check_packs.setProperty("class", "adco")

        btn_layout.addWidget(self._btn_add)
        btn_layout.addWidget(self._btn_add_folder)
        btn_layout.addWidget(self._btn_remove)
        btn_layout.addWidget(self._btn_check_packs)
        btn_layout.addStretch()

        layout.addWidget(btn_row)

        # ── Achievement indicator ────────────────────────────────────
        self.achievement_indicator = AchievementIndicator()
        layout.addWidget(self.achievement_indicator)

        # ── Output group ─────────────────────────────────────────────
        self._output_group = QGroupBox("")
        output_layout = QVBoxLayout(self._output_group)

        # Directory row
        dir_row = QHBoxLayout()
        self._out_label = QLabel()
        dir_row.addWidget(self._out_label)
        self._entry_output_dir = QLineEdit()
        self._entry_output_dir.setPlaceholderText("")
        self._btn_select_output = QPushButton()
        dir_row.addWidget(self._entry_output_dir, 1)
        dir_row.addWidget(self._btn_select_output)
        output_layout.addLayout(dir_row)

        # Format row
        format_row = QHBoxLayout()
        self._format_label = QLabel()
        self._format_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        self._format_combo = QComboBox()
        self._format_combo.addItem("", "mcaddon")
        self._format_combo.addItem("", "mcpack")
        self._format_combo.addItem("", "zip")
        format_row.addWidget(self._format_label)
        format_row.addWidget(self._format_combo, 1)
        output_layout.addLayout(format_row)

        layout.addWidget(self._output_group)

        # ── Progress bar ─────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # ── Start / Cancel buttons ────────────────────────────────────
        btn_merge_row = QHBoxLayout()
        self._btn_start = QPushButton()
        self._btn_start.setProperty("class", "primary")
        self._btn_start.setMinimumHeight(56)
        self._btn_start.setMinimumWidth(180)
        btn_merge_row.addWidget(self._btn_start)

        self._btn_cancel = QPushButton()
        self._btn_cancel.setProperty("class", "danger")
        self._btn_cancel.setMinimumHeight(56)
        self._btn_cancel.setEnabled(False)
        btn_merge_row.addWidget(self._btn_cancel)

        layout.addLayout(btn_merge_row)

        # ── Status label (hidden by default) ─────────────────────────
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #5CE3E6; font-weight: 600;")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.hide()
        layout.addWidget(self._status_label)

        layout.addStretch()

    def retranslate_ui(self):
        self._files_group.setTitle(_tr("merger.group.files", "Files"))
        self._output_group.setTitle(_tr("merger.group.output", "Output"))
        self._btn_add.setText(_tr("merger.add_files", "Add Files"))
        self._btn_add_folder.setText(_tr("merger.add_folder", "Add Folder"))
        self._btn_remove.setText(_tr("merger.remove_selected", "Remove Selected"))
        self._btn_check_packs.setText(_tr("merger.check_packs", "Check Packs"))
        self._out_label.setText(_tr("merger.output_dir", "Output Directory:"))
        self._entry_output_dir.setPlaceholderText(_tr("merger.output_dir_ph", "Select output directory..."))
        self._btn_select_output.setText(_tr("common.browse", "Browse..."))
        self._format_label.setText(_tr("merger.output_format", "Output Format:"))
        self._format_combo.setItemText(0, _tr("merger.fmt.mcaddon", ".mcaddon  (combined RP + BP)"))
        self._format_combo.setItemText(1, _tr("merger.fmt.mcpack", ".mcpack   (separate RP / BP)"))
        self._format_combo.setItemText(2, _tr("merger.fmt.zip", ".zip      (plain archives)"))
        self._format_combo.setToolTip(_tr("merger.fmt.tooltip",
            "mcaddon — single file with both packs (double-click to import)\n"
            "mcpack  — two separate .mcpack files (one RP, one BP)\n"
            "zip     — plain .zip archives"))
        self._btn_start.setText(_tr("merger.start_merging", "Start Merging"))
        self._btn_cancel.setText(_tr("common.cancel", "Cancel"))
        self.achievement_indicator.retranslate_ui()

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def btn_add(self):
        return self._btn_add

    @property
    def btn_add_folder(self):
        return self._btn_add_folder

    @property
    def btn_remove(self):
        return self._btn_remove

    @property
    def btn_check_packs(self):
        return self._btn_check_packs

    @property
    def btn_select_output(self):
        return self._btn_select_output

    @property
    def btn_start(self):
        return self._btn_start

    @property
    def btn_cancel(self):
        return self._btn_cancel

    @property
    def entry_output_dir(self):
        return self._entry_output_dir

    @property
    def format_combo(self):
        return self._format_combo

    def get_output_format(self):
        """Return selected output format: 'mcaddon', 'mcpack', or 'zip'."""
        return self._format_combo.currentData() or "mcaddon"

    def set_output_format(self, fmt):
        idx = self._format_combo.findData(fmt)
        if idx >= 0:
            self._format_combo.setCurrentIndex(idx)

    @property
    def status_label(self):
        return self._status_label

    def set_status(self, text):
        """Update the status label text."""
        self._status_label.setText(text)
        self._status_label.show()

    def clear_status(self):
        self._status_label.hide()

    def get_file_list(self):
        """Return list of file paths currently in the list widget."""
        paths = []
        for i in range(self.file_list_box.count()):
            item = self.file_list_box.item(i)
            if item:
                paths.append(item.text())
        return paths

    def set_file_list(self, paths):
        """Replace the entire file list."""
        self.file_list_box.clear()
        for p in paths:
            self.file_list_box.addItem(p)

    def set_progress(self, value):
        """Set progress bar value (0-100)."""
        self.progress_bar.setValue(value)

    def set_merge_running(self, running):
        """Enable/disable controls during merge."""
        self._btn_add.setEnabled(not running)
        self._btn_add_folder.setEnabled(not running)
        self._btn_remove.setEnabled(not running)
        self._btn_check_packs.setEnabled(not running)
        self._btn_select_output.setEnabled(not running)
        self._btn_start.setEnabled(not running)
        self._btn_cancel.setEnabled(running)
        self._entry_output_dir.setEnabled(not running)
        self._format_combo.setEnabled(not running)
