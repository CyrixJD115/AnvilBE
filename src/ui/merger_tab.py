"""
Merger tab — the primary tab for addon pack merging.
Provides file list, controls, progress tracking, and triggers the merge pipeline.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget,
    QPushButton, QLineEdit, QProgressBar, QLabel
)
from PySide6.QtCore import Qt
from src.ui.widgets import AchievementIndicator


class MergerTab(QWidget):
    """
    Main merger tab with file selection, output configuration, and merge controls.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Files group ──────────────────────────────────────────────
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(files_group)

        self.file_list_box = QListWidget()
        self.file_list_box.setMinimumHeight(220)
        self.file_list_box.setAlternatingRowColors(False)
        self.file_list_box.setSelectionMode(QListWidget.ExtendedSelection)
        files_layout.addWidget(self.file_list_box)

        layout.addWidget(files_group)

        # ── Button row ───────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self._btn_add = QPushButton("Add Files")
        self._btn_remove = QPushButton("Remove Selected")
        self._btn_remove.setProperty("class", "danger")
        self._btn_check_packs = QPushButton("Check Packs")
        self._btn_check_packs.setProperty("class", "adco")

        btn_layout.addWidget(self._btn_add)
        btn_layout.addWidget(self._btn_remove)
        btn_layout.addWidget(self._btn_check_packs)
        btn_layout.addStretch()

        layout.addWidget(btn_row)

        # ── Achievement indicator ────────────────────────────────────
        self.achievement_indicator = AchievementIndicator()
        layout.addWidget(self.achievement_indicator)

        # ── Output group ─────────────────────────────────────────────
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout(output_group)

        out_label = QLabel("Output Directory:")
        self._entry_output_dir = QLineEdit()
        self._entry_output_dir.setPlaceholderText("Select output directory...")
        self._btn_select_output = QPushButton("Browse...")

        output_layout.addWidget(out_label)
        output_layout.addWidget(self._entry_output_dir, 1)
        output_layout.addWidget(self._btn_select_output)

        layout.addWidget(output_group)

        # ── Progress bar ─────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # ── Start / Cancel buttons ────────────────────────────────────
        btn_merge_row = QHBoxLayout()
        self._btn_start = QPushButton("Start Merging")
        self._btn_start.setProperty("class", "primary")
        self._btn_start.setMinimumHeight(48)
        btn_merge_row.addWidget(self._btn_start)

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setProperty("class", "danger")
        self._btn_cancel.setMinimumHeight(48)
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

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def btn_add(self):
        return self._btn_add

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
        self._btn_remove.setEnabled(not running)
        self._btn_check_packs.setEnabled(not running)
        self._btn_select_output.setEnabled(not running)
        self._btn_start.setEnabled(not running)
        self._btn_cancel.setEnabled(running)
        self._entry_output_dir.setEnabled(not running)
