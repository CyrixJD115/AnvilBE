"""
MergerTab — the primary dashboard for Anvil-MC pack merging.

Replaces the old flat tab with a streamlined workspace:
  • file/folder drop zones (with green-highlight feedback),
  • a prominent "Run Pipeline" action block,
  • compact configuration toggle chips mirrored to settings,
  • inline progress + status, and
  • a drag-aware output directory field.

All public accessors consumed by ``app.py``'s pipeline logic are preserved
unchanged so the background merge worker stays fully wired.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QPushButton,
    QLineEdit, QProgressBar, QLabel, QComboBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from src.ui.widgets import AchievementIndicator, DropFileList
from src.ui.drop_widgets import DropLineEdit
from src.core.i18n import _tr


class _NoOpDropZone(QObject):
    """Backward-compat shim. The window-wide :class:`DropOverlay` now owns
    drag-and-drop; this exposes a ``paths_dropped`` signal so legacy
    ``merger_tab.drop_zone.paths_dropped.connect(...)`` calls remain valid
    (they're superseded by the overlay's own ``paths_dropped`` signal)."""

    paths_dropped = Signal(list)


class MergerTab(QWidget):
    """
    Main dashboard workspace for merging Minecraft Bedrock addon packs.

    Mirrors the original API so the merge worker / app controller remain
    unchanged, while restructuring the layout around the file list, output
    config, and a Run Pipeline action block. Configuration toggles live in
    the Settings view; drag-and-drop is handled window-wide by the overlay.
    """

    # Emitted when a pack file/folder is dropped onto the file list.
    paths_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    # ──────────────────────────────────────────────────────────────────
    # UI SETUP — kept as one descriptive method; layout separated from
    # event handling.
    # ──────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        # Wrap everything in a scroll area so the dashboard stays usable
        # at small window sizes.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setProperty("class", "view-scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        host = QWidget()
        scroll.setWidget(host)

        layout = QVBoxLayout(host)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Heading ───────────────────────────────────────────────────
        self._heading = QLabel()
        self._heading.setStyleSheet("color: #7CBD4D; font-size: 18pt; font-weight: 800;")
        layout.addWidget(self._heading)

        self._subheading = QLabel()
        self._subheading.setStyleSheet("color: #888888; font-size: 10pt;")
        self._subheading.setWordWrap(True)
        layout.addWidget(self._subheading)

        # Drag-and-drop is handled window-wide by the DropOverlay, so the
        # dashboard itself shows no drop box/hint. Keep a no-op stub for
        # backward compatibility with legacy drop_zone.paths_dropped wiring.
        self.drop_zone = _NoOpDropZone()

        # ── Files group ───────────────────────────────────────────────
        self._files_group = QGroupBox("")
        # Expanding vertical policy: this group absorbs extra window height
        # so the file list grows with the window (min 160px preserved).
        sp = self._files_group.sizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        self._files_group.setSizePolicy(sp)
        files_layout = QVBoxLayout(self._files_group)

        self.file_list_box = DropFileList()
        self.file_list_box.setMinimumHeight(160)
        self.file_list_box.setAlternatingRowColors(False)
        self.file_list_box.setSelectionMode(QListWidget.ExtendedSelection)
        # The list absorbs all spare vertical space: expanding policy plus a
        # stretch factor so it grows with the window while the buttons below
        # keep their natural height. Minimum height (160px) is preserved.
        self.file_list_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        files_layout.addWidget(self.file_list_box, 1)

        # Button row
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

        files_layout.addWidget(btn_row)
        # Stretch factor 1 → the files group grows to fill spare vertical
        # space; the widgets below keep their natural (fixed) heights.
        layout.addWidget(self._files_group, 1)

        # ── Achievement indicator ─────────────────────────────────────
        self.achievement_indicator = AchievementIndicator()
        layout.addWidget(self.achievement_indicator)

        # ── Output group ──────────────────────────────────────────────
        self._output_group = QGroupBox("")
        output_layout = QVBoxLayout(self._output_group)

        # Drag-aware output directory row
        dir_row = QHBoxLayout()
        self._out_label = QLabel()
        dir_row.addWidget(self._out_label)
        self._entry_output_dir = DropLineEdit()
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

        # ── Run Pipeline action block ─────────────────────────────────
        action = QFrame()
        action.setProperty("class", "action-block")
        action_layout = QVBoxLayout(action)
        action_layout.setContentsMargins(16, 14, 16, 16)
        action_layout.setSpacing(8)

        self._action_title = QLabel()
        self._action_title.setProperty("class", "action-title")
        action_layout.addWidget(self._action_title)

        self._action_subtitle = QLabel()
        self._action_subtitle.setProperty("class", "action-subtitle")
        self._action_subtitle.setWordWrap(True)
        action_layout.addWidget(self._action_subtitle)

        # Inline progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_layout.addWidget(self.progress_bar)

        # Status label (hidden by default)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #5CE3E6; font-weight: 600;")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.hide()
        action_layout.addWidget(self._status_label)

        # Start / Cancel buttons
        btn_merge_row = QHBoxLayout()
        self._btn_start = QPushButton()
        self._btn_start.setProperty("class", "primary")
        self._btn_start.setMinimumHeight(52)
        self._btn_start.setMinimumWidth(180)
        btn_merge_row.addWidget(self._btn_start)

        self._btn_cancel = QPushButton()
        self._btn_cancel.setProperty("class", "danger")
        self._btn_cancel.setMinimumHeight(52)
        self._btn_cancel.setEnabled(False)
        btn_merge_row.addWidget(self._btn_cancel)

        action_layout.addLayout(btn_merge_row)
        layout.addWidget(action)

    # ──────────────────────────────────────────────────────────────────
    # i18n
    # ──────────────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._heading.setText(_tr("dashboard.heading", "Merge Pipeline"))
        self._subheading.setText(_tr("dashboard.subheading",
            "Add your .mcpack / .mcaddon files or pack folders, choose an output, "
            "and run the merge. You can drag files anywhere on the window."))
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
        # Inline tooltips (micro-documentation)
        self._btn_check_packs.setToolTip(_tr("tip.check_packs",
            "Scans loaded packs and groups them by their Script API version, "
            "warning you about cross-version incompatibilities."))
        self._btn_start.setText(_tr("dashboard.run_pipeline", "Merge"))
        self._btn_start.setToolTip(_tr("tip.run_pipeline",
            "Validates packs, merges JSON, resolves identifier conflicts, "
            "and packages the output in your chosen format."))
        self._btn_cancel.setText(_tr("common.cancel", "Cancel"))
        self._action_title.setText(_tr("dashboard.action_title", "Merge"))
        self._action_subtitle.setText(_tr("dashboard.action_subtitle",
            "Validates, merges, and packages all loaded packs."))
        self.achievement_indicator.retranslate_ui()

    # ──────────────────────────────────────────────────────────────────
    # Public accessors — preserved exactly from the old tab API.
    # ──────────────────────────────────────────────────────────────────

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

    # ── Format helpers ────────────────────────────────────────────────
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
        """Update the inline status label text."""
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
