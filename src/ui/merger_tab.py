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
    QLineEdit, QProgressBar, QLabel, QComboBox, QFrame, QScrollArea,
    QApplication, QStyle
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
    unchanged, while restructuring the layout into drop zones + an action
    block + compact toggles.
    """

    # Emitted when a pack file/folder is dropped onto the main drop zone.
    paths_dropped = Signal(list)
    # Emitted when a quick-toggle chip changes — host persists it.
    option_changed = Signal(str, bool)

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

        # ── Hint strip (drag anywhere on the window — overlay handles it) ──
        self._drop_hint = QWidget()
        self._drop_hint.setStyleSheet(
            "QWidget { background-color: #1F2D2D; "
            "border: 2px dashed #3D6A6A; }")
        hint_layout = QHBoxLayout(self._drop_hint)
        hint_layout.setContentsMargins(14, 10, 14, 10)
        hint_layout.setSpacing(8)
        hint_layout.setAlignment(Qt.AlignCenter)

        self._drop_hint_icon = QLabel()
        self._drop_hint_icon.setFixedSize(16, 16)
        self._drop_hint_icon.setAlignment(Qt.AlignCenter)
        hint_layout.addWidget(self._drop_hint_icon)

        self._drop_hint_text = QLabel()
        self._drop_hint_text.setStyleSheet(
            "QLabel { color: #5CE3E6; background-color: transparent; "
            "border: none; font-weight: 600; }")
        hint_layout.addWidget(self._drop_hint_text)
        layout.addWidget(self._drop_hint)
        self._set_drop_hint_icon()
        # Backward-compat stub: the window-wide DropOverlay now owns drag-drop,
        # but app.py historically connected drop_zone.paths_dropped.
        self.drop_zone = _NoOpDropZone()

        # ── Files group ───────────────────────────────────────────────
        self._files_group = QGroupBox("")
        files_layout = QVBoxLayout(self._files_group)

        self.file_list_box = DropFileList()
        self.file_list_box.setMinimumHeight(160)
        self.file_list_box.setAlternatingRowColors(False)
        self.file_list_box.setSelectionMode(QListWidget.ExtendedSelection)
        files_layout.addWidget(self.file_list_box)

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
        layout.addWidget(self._files_group)

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

        # ── Compact configuration toggle chips ────────────────────────
        self._toggles_group = QGroupBox("")
        toggles_layout = QVBoxLayout(self._toggles_group)
        toggles_layout.setSpacing(8)

        self._chk_modpack = self._make_chip()
        self._chk_merge_version = self._make_chip()
        self._chk_customize = self._make_chip()

        toggles_layout.addWidget(self._chk_modpack)
        toggles_layout.addWidget(self._chk_merge_version)
        toggles_layout.addWidget(self._chk_customize)
        layout.addWidget(self._toggles_group)

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

        layout.addStretch()

        # ── Internal signal wiring ────────────────────────────────────
        # The shim drop_zone keeps a paths_dropped signal for backward compat;
        # the window-wide DropOverlay is the real drag-drop surface now.
        self._chk_modpack.toggled.connect(lambda v: self.option_changed.emit("modpack_organization", v))
        self._chk_merge_version.toggled.connect(lambda v: self.option_changed.emit("merge_by_version", v))
        self._chk_customize.toggled.connect(lambda v: self.option_changed.emit("customize_pack_after_merge", v))

    def _make_chip(self) -> QPushButton:
        # Reuse QCheckBox for the chip styling defined in dashboard_theme.qss.
        from PySide6.QtWidgets import QCheckBox
        chip = QCheckBox()
        chip.setProperty("class", "chip")
        chip.setStyleSheet("color: #C6C6C6;")
        chip.setCursor(Qt.PointingHandCursor)
        return chip

    def _set_drop_hint_icon(self):
        """Render the built-in down-arrow icon into the drop-hint strip."""
        app = QApplication.instance()
        if app is None:
            return
        icon = app.style().standardIcon(QStyle.SP_ArrowDown)
        self._drop_hint_icon.setPixmap(icon.pixmap(16, 16))

    # ──────────────────────────────────────────────────────────────────
    # i18n
    # ──────────────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._heading.setText(_tr("dashboard.heading", "Merge Pipeline"))
        self._subheading.setText(_tr("dashboard.subheading",
            "Drop your .mcpack / .mcaddon files or pack folders below, choose an output, "
            "and run the merge. Configuration toggles mirror your settings."))
        self._files_group.setTitle(_tr("merger.group.files", "Files"))
        self._output_group.setTitle(_tr("merger.group.output", "Output"))
        self._toggles_group.setTitle(_tr("dashboard.group.options", "Quick Options"))
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
        self._chk_modpack.setText(_tr("settings.modpack_organization",
            "Modpack organization (group by source pack)"))
        self._chk_merge_version.setText(_tr("settings.merge_by_version",
            "Merge by @minecraft/server version"))
        self._chk_customize.setText(_tr("settings.customize_before_merge",
            "Show pack customization dialog before merge"))
        # Inline tooltips (micro-documentation)
        self._chk_modpack.setToolTip(_tr("tip.modpack_org",
            "Prefixes every merged file with its source pack name so you can "
            "trace where each asset originated."))
        self._chk_merge_version.setToolTip(_tr("tip.merge_by_version",
            "Splits output into one BP/RP pair per @minecraft/server API "
            "version, so incompatible script packs stay separate."))
        self._chk_customize.setToolTip(_tr("tip.customize",
            "Opens a dialog before the merge to set the pack name, author, "
            "description, and icon."))
        self._btn_check_packs.setToolTip(_tr("tip.check_packs",
            "Scans loaded packs and groups them by their Script API version, "
            "warning you about cross-version incompatibilities."))
        self._btn_start.setText(_tr("dashboard.run_pipeline", "Run Pipeline"))
        self._btn_start.setToolTip(_tr("tip.run_pipeline",
            "Validates packs, merges JSON, resolves identifier conflicts, "
            "and packages the output in your chosen format."))
        self._btn_cancel.setText(_tr("common.cancel", "Cancel"))
        self._action_title.setText(_tr("dashboard.action_title", "Run Pipeline"))
        self._action_subtitle.setText(_tr("dashboard.action_subtitle",
            "Validates, merges, and packages all loaded packs."))
        self._drop_hint_text.setText(_tr("dashboard.drop_hint_strip",
            "Drag .mcpack / .mcaddon / folders anywhere — or click Add Files"))
        self._set_drop_hint_icon()
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

    # ── Quick-option chips (new) ──────────────────────────────────────
    @property
    def chk_modpack(self):
        return self._chk_modpack

    @property
    def chk_merge_version(self):
        return self._chk_merge_version

    @property
    def chk_customize(self):
        return self._chk_customize

    def set_option(self, name: str, value: bool):
        """Set a quick-option chip without re-emitting option_changed."""
        chip = {
            "modpack_organization": self._chk_modpack,
            "merge_by_version": self._chk_merge_version,
            "customize_pack_after_merge": self._chk_customize,
        }.get(name)
        if chip is not None:
            chip.blockSignals(True)
            chip.setChecked(bool(value))
            chip.blockSignals(False)

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
        self._chk_modpack.setEnabled(not running)
        self._chk_merge_version.setEnabled(not running)
        self._chk_customize.setEnabled(not running)
