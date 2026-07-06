"""
Anvil-MC main application window.
QMainWindow with tabbed interface for Minecraft Bedrock addon merging.
"""
import os as _os
import sys as _sys
import json as _json
import zipfile as _zipfile
import shutil as _shutil
import re as _re
import uuid as _uuid
import datetime as _datetime
import tempfile as _tempfile
import logging as _logging
import traceback as _traceback
import threading as _threading
import csv as _csv
import fnmatch as _fnmatch
from collections import defaultdict
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMessageBox, QStatusBar, QMenuBar, QFileDialog,
    QLabel, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# ── Core modules ─────────────────────────────────────────────────────
from src.core.file_utils import (
    strip_bom, read_text_file_utf8_strip_bom, write_text_file_utf8,
    safe_decode, read_json_safe
)
from src.core.i18n import _, _f, _tr, _init_translations, _tr_load
from src.core.pack_utils import (
    is_pack_folder, has_pack_icon, validate_pack_folder,
    recursive_extract_pack, folder_to_mcpack, zip_pack_folder,
    find_valid_packs, get_pack_manifest_data, get_pack_icon_from_zip
)
from src.core.merger import UniversalJsonMerger
from src.core.identifier_manager import IdentifierManager

# ── UI tabs ──────────────────────────────────────────────────────────
from src.ui.merger_tab import MergerTab
from src.ui.mcpacker_tab import MCPackerTab
from src.ui.list_maker_tab import ListMakerTab
from src.ui.help_tab import HelpTab
from src.ui.settings_tab import SettingsTab
from src.ui.console_tab import ConsoleTab

# ── Dialogs ──────────────────────────────────────────────────────────
from src.ui.dialogs import (
    ConflictResolutionDialog,
    VersionCheckDialog, PackCustomizationDialog, AboutDialog
)

# ── Workers ──────────────────────────────────────────────────────────
from src.workers.merge_worker import MergeWorkerThread

# ── Fixers Framework ─────────────────────────────────────────────────
try:
    from src import fixers as _fixers_mod
    _FIXERS = _fixers_mod.load_fixers()
    if _FIXERS:
        _logging.info(f"[Fixers] Loaded {len(_FIXERS)} addon fixer(s)")
    from src.fixers.universal_compatibility import UniversalCompatibilityPatcher
    _UNIVERSAL_PATCHER = UniversalCompatibilityPatcher()
except Exception:
    _fixers_mod = None
    _FIXERS = []
    _UNIVERSAL_PATCHER = None

# ── App version ──────────────────────────────────────────────────────
APP_VERSION = "7.0.2"

# Mergeable files — JSON files that can be merged from multiple packs
_MERGEABLE_FILES = {
    "item_texture.json", "terrain_texture.json", "tick.json", "sounds.json",
    "blocks.json", "biomes_client.json", "sound_definitions.json",
    "music_definitions.json", "_ui_defs.json", "hud_screen.json",
    "npc_interact_screen.json", "_global_variables.json", "ui_common.json",
    "splashes.json", "player.animation_controllers.json", "player.animation.json",
    "player.render_controllers.json", "crafting_item_catalog.json",
}
_LIST_MERGEABLE_FILES = {"flipbook_textures.json", "textures_list.json"}


def _load_stylesheet():
    """Load the QSS stylesheet from the theme directory."""
    qss_path = Path(__file__).parent / "theme" / "minecraft_theme.qss"
    try:
        with open(qss_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        _logging.warning(f"Stylesheet not found: {qss_path}")
        return ""


class AutoBEWindow(QMainWindow):
    """
    Main application window for Anvil-MC.
    Handles all GUI components, merge pipeline logic, and state management.
    """

    def __init__(self):
        super().__init__()

        # ── State ────────────────────────────────────────────────────
        self._files = []
        self._out_dir = _os.path.expanduser("~")
        self._output_format = "mcaddon"
        self.worker_thread = None

        # Version tracking
        self.highest_bp_version = [1, 0, 0]
        self.highest_rp_version = [1, 0, 0]
        self.highest_server_version_full = '1.13.0'
        self.highest_server_ui_version_full = '1.2.0'
        self.highest_gametest_version_full = None

        # Settings
        self._settings = self._load_settings()
        self._current_lang = self._settings.get("lang", "en")
        self.modpack_organization = self._settings.get("modpack_organization", False)
        self.merge_by_version = self._settings.get("merge_by_version", False)
        self.customize_pack_after_merge = self._settings.get("customize_pack_after_merge", True)
        self.show_linked_packs_after_merge = self._settings.get("show_linked_packs_after_merge", False)
        self._output_format = self._settings.get("output_format", "mcaddon")

        # Merge progress
        self._progress = {'value': 0, 'maximum': 100}
        self._merge_start_ts = 0
        self._merge_cancelled = False

        # ── Init i18n ────────────────────────────────────────────────
        _init_translations()
        if self._current_lang != "en":
            _tr_load(self._current_lang)

        # ── Setup UI ─────────────────────────────────────────────────
        self._setup_ui()
        self._load_styles()
        self._connect_signals()

        # Apply initial output dir from settings
        saved_out = self._settings.get("output_dir", "")
        if saved_out and _os.path.isdir(saved_out):
            self._out_dir = saved_out
            self.merger_tab.entry_output_dir.setText(saved_out)

        # Apply saved output format
        self.merger_tab.set_output_format(self._output_format)

    # ──────────────────────────────────────────────────────────────────
    # UI SETUP
    # ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        """Set up the main window, tabs, menus, and status bar."""
        self.setWindowTitle("Anvil-MC")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)

        # Central widget
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Tab widget
        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)

        # Create tabs
        self.merger_tab = MergerTab()
        self.mcpacker_tab = MCPackerTab()
        self.list_maker_tab = ListMakerTab()
        self.settings_tab = SettingsTab()
        self.help_tab = HelpTab()
        self.console_tab = ConsoleTab()

        self.notebook.addTab(self.merger_tab, "")
        self.notebook.addTab(self.mcpacker_tab, "")
        self.notebook.addTab(self.list_maker_tab, "")
        self.notebook.addTab(self.settings_tab, "")
        self.notebook.addTab(self.help_tab, "")
        self.notebook.addTab(self.console_tab, "")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.mode_label = QLabel(_tr("status.ready", "Ready"))
        self.mode_label.setProperty("class", "status-mode")
        self.status_bar.addWidget(self.mode_label, 1)
        self.trademark_label = QLabel("Anvil-MC")
        self.trademark_label.setProperty("class", "trademark")
        self.status_bar.addPermanentWidget(self.trademark_label)

        # Menu bar
        self._create_menu_bar()
        # Apply initial translations to tabs + menus
        self._retranslate_ui()

    def _create_menu_bar(self):
        """Create the menu bar with File and Help menus (text set via _retranslate_ui)."""
        menubar = self.menuBar()
        self._menu_tr_targets = []  # list of (setter, key, fallback)

        file_menu = menubar.addMenu("")
        self._menu_tr_targets.append((file_menu.setTitle, "menu.file", "&File"))
        act = file_menu.addAction("", self._add_files, "Ctrl+O")
        self._menu_tr_targets.append((act.setText, "menu.add_files", "Add &Files"))
        file_menu.addSeparator()
        act = file_menu.addAction("", self.close, "Ctrl+Q")
        self._menu_tr_targets.append((act.setText, "menu.exit", "E&xit"))

        help_menu = menubar.addMenu("")
        self._menu_tr_targets.append((help_menu.setTitle, "menu.help", "&Help"))
        act = help_menu.addAction("", self._show_help, "F1")
        self._menu_tr_targets.append((act.setText, "menu.help_contents", "&Help"))
        help_menu.addSeparator()
        act = help_menu.addAction("", self._show_about)
        self._menu_tr_targets.append((act.setText, "menu.about", "&About"))

    def _retranslate_ui(self):
        """Re-apply translatable UI strings (tabs + menus) after a language change."""
        tabs = [
            (0, "tabs.merger", "Merger"),
            (1, "tabs.pack_utility", "Pack Utility"),
            (2, "tabs.pack_organizer", "Pack Organizer"),
            (3, "tabs.settings", "Settings"),
            (4, "tabs.help", "Help"),
            (5, "tabs.console", "Console"),
        ]
        for idx, key, fallback in tabs:
            self.notebook.setTabText(idx, _tr(key, fallback))
        for setter, key, fallback in getattr(self, "_menu_tr_targets", []):
            setter(_tr(key, fallback))
        # Retranslate every child tab/widget
        for child in (self.merger_tab, self.mcpacker_tab, self.list_maker_tab,
                      self.settings_tab, self.help_tab, self.console_tab):
            if hasattr(child, "retranslate_ui"):
                child.retranslate_ui()

    def _load_styles(self):
        """Apply the QSS stylesheet."""
        qss = _load_stylesheet()
        if qss:
            self.setStyleSheet(qss)

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Merger tab
        self.merger_tab.btn_add.clicked.connect(self._add_files)
        self.merger_tab.btn_add_folder.clicked.connect(self._add_folder)
        self.merger_tab.btn_remove.clicked.connect(self._remove_files)
        self.merger_tab.btn_check_packs.clicked.connect(self._check_packs)
        self.merger_tab.btn_select_output.clicked.connect(self._select_output_dir)
        self.merger_tab.btn_start.clicked.connect(self._start_merge)
        self.merger_tab.btn_cancel.clicked.connect(self._cancel_merge)
        self.merger_tab.file_list_box.files_dropped.connect(self._on_files_dropped)

        # MCPacker tab
        self.mcpacker_tab.btn_add.clicked.connect(self._mcpacker_add)
        self.mcpacker_tab.btn_remove.clicked.connect(self._mcpacker_remove)
        self.mcpacker_tab.btn_start.clicked.connect(self._mcpacker_start)
        self.mcpacker_tab.btn_browse.clicked.connect(self._mcpacker_browse_output)

        # List Maker tab
        self.list_maker_tab.btn_add_files.clicked.connect(self._list_maker_add)
        self.list_maker_tab.btn_clear.clicked.connect(self._list_maker_clear)
        self.list_maker_tab.btn_organize.clicked.connect(self._list_maker_organize)
        self.list_maker_tab.btn_export.clicked.connect(self._list_maker_export)

        # Settings tab
        self.settings_tab.btn_save.clicked.connect(self._save_settings_from_tab)
        self.settings_tab.btn_browse.clicked.connect(self._settings_browse_output)
        self.settings_tab.set_settings(self._settings)

    # ──────────────────────────────────────────────────────────────────
    # SETTINGS
    # ──────────────────────────────────────────────────────────────────

    def _get_settings_path(self):
        """Get the path for the settings file."""
        base = _os.path.join(_os.path.expanduser("~"), ".anvil-mc")
        try:
            _os.makedirs(base, exist_ok=True)
        except Exception:
            base = _os.path.dirname(_os.path.abspath(__file__))
        return _os.path.join(base, "settings.json")

    def _load_settings(self):
        """Load settings from JSON file."""
        path = self._get_settings_path()
        try:
            if _os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return _json.load(f)
        except Exception as e:
            _logging.warning(f"Could not load settings: {e}")
        return {}

    def _save_settings(self):
        """Save current settings to JSON file."""
        path = self._get_settings_path()
        settings = {
            "lang": self._current_lang,
            "output_dir": self._out_dir,
            "modpack_organization": self.modpack_organization,
            "merge_by_version": self.merge_by_version,
            "customize_pack_after_merge": self.customize_pack_after_merge,
            "show_linked_packs_after_merge": self.show_linked_packs_after_merge,
            "output_format": getattr(self, '_output_format', 'mcaddon'),
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(settings, f, indent=2)
        except Exception as e:
            _logging.warning(f"Could not save settings: {e}")

    # ──────────────────────────────────────────────────────────────────
    # FILE SELECTION
    # ──────────────────────────────────────────────────────────────────

    def _add_files_to_list(self, paths):
        """Add paths (files or dirs) to the merger file list, deduplicating."""
        existing = self.merger_tab.get_file_list()
        existing_set = set(existing)
        added = 0
        for p in paths:
            if p not in existing_set:
                existing.append(p)
                existing_set.add(p)
                added += 1
        if added > 0:
            self.merger_tab.set_file_list(existing)
            self.mode_label.setText(_tr("status.files_loaded", "{n} file(s) loaded").format(n=len(existing)))
            self.merger_tab.achievement_indicator.set_status_unknown()

    def _add_files(self):
        """Open file dialog to add pack files (.mcpack/.mcaddon/.zip)."""
        files, _ = QFileDialog.getOpenFileNames(
            self, _tr("filedialog.select_pack_files", "Select Pack Files"),
            self._out_dir,
            _tr("filedialog.pack_filter", "Minecraft Packs (*.mcpack *.mcaddon *.zip);;All Files (*)"))
        if files:
            self._add_files_to_list(files)

    def _add_folder(self):
        """Open directory dialog to add a pack folder."""
        folder = QFileDialog.getExistingDirectory(
            self, _tr("filedialog.select_pack_folder", "Select Pack Folder"), self._out_dir)
        if folder:
            self._add_files_to_list([folder])

    def _on_files_dropped(self, paths):
        """Handle files/folders dropped onto the file list."""
        self._add_files_to_list(paths)

    def _remove_files(self):
        """Remove selected files from the merger tab."""
        selected = self.merger_tab.file_list_box.selectedItems()
        if not selected:
            return

        current = self.merger_tab.get_file_list()
        remove_set = set(item.text() for item in selected)
        remaining = [f for f in current if f not in remove_set]
        self.merger_tab.set_file_list(remaining)
        self.mode_label.setText(_tr("status.files_loaded", "{n} file(s) loaded").format(n=len(remaining)))

    def _select_output_dir(self):
        """Open directory dialog for output selection."""
        directory = QFileDialog.getExistingDirectory(
            self, _tr("filedialog.select_output_dir", "Select Output Directory"), self._out_dir)
        if directory:
            self._out_dir = directory
            self.merger_tab.entry_output_dir.setText(directory)
            self._output_format = self.merger_tab.get_output_format()
            self._save_settings()

    # ──────────────────────────────────────────────────────────────────
    # CHECK PACKS
    # ──────────────────────────────────────────────────────────────────

    def _check_packs(self):
        """Scan loaded packs and show version grouping dialog."""
        files = self.merger_tab.get_file_list()
        if not files:
            QMessageBox.warning(self, _tr("msg.no_files", "No Files"),
                                _tr("msg.add_files_first", "Please add pack files first."))
            return

        self.mode_label.setText(_tr("status.scanning_packs", "Scanning packs..."))
        self.merger_tab.achievement_indicator.set_status_unknown()
        QApplication.processEvents()

        version_groups = defaultdict(list)
        failed = 0
        any_scripts = False

        for file_path in files:
            manifest = get_pack_manifest_data(file_path)
            if not manifest:
                failed += 1
                continue

            # Display name from manifest header, fall back to filename
            header = manifest.get('header', {}) or {}
            pack_name = header.get('name') or _os.path.basename(file_path)

            # Pack type (RP / BP / both)
            modules = manifest.get('modules', []) or []
            is_rp = any(m.get('type', '').lower() == 'resources' for m in modules)
            is_bp = any(m.get('type', '').lower() in ('data', 'script') for m in modules)
            types = []
            if is_rp:
                types.append('RP')
            if is_bp:
                types.append('BP')
            pack_type = '+'.join(types) if types else '?'

            if any(m.get('type', '').lower() == 'script' for m in modules):
                any_scripts = True

            # Script API dependencies
            scripts = []
            server_ver = "No Script API"
            for dep in manifest.get('dependencies', []) or []:
                mod_name = dep.get('module_name', '')
                if not mod_name.startswith('@minecraft/'):
                    continue
                ver = dep.get('version', '')
                if isinstance(ver, list):
                    ver = '.'.join(str(v) for v in ver)
                scripts.append(f"{mod_name} {ver}".strip())
                if mod_name == '@minecraft/server':
                    server_ver = ver or 'unspecified'

            version_groups[server_ver].append({
                'name': pack_name,
                'type': pack_type,
                'scripts': scripts,
                'file_path': file_path,
            })

        # Show version check dialog
        dialog = VersionCheckDialog(dict(version_groups), failed, self)
        dialog.exec()

        # Proactive suggestion: enable merge-by-version if the user opted in
        if getattr(dialog, 'merge_by_version_requested', False) and not self.merge_by_version:
            self.merge_by_version = True
            self.settings_tab.chk_merge_version.setChecked(True)
            self._save_settings()
            self.merger_tab.set_status(_tr("status.merge_by_version_enabled", "Merge by version enabled from pack check."))
            _logging.info("Merge-by-version enabled via Check Packs suggestion")

        # Reflect actual achievement compatibility based on script presence
        self.merger_tab.achievement_indicator.set_status(not any_scripts)
        self.mode_label.setText(f"{len(files)} file(s) loaded")

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — START
    # ──────────────────────────────────────────────────────────────────

    def _build_customization_prefill(self, files):
        """Build a prefill dict (name/author/description) from the first pack's manifest."""
        prefill = {}
        if files:
            manifest = get_pack_manifest_data(files[0])
            if manifest:
                header = manifest.get('header', {}) or {}
                if header.get('name'):
                    prefill['name'] = header['name']
                authors = header.get('authors')
                if isinstance(authors, list) and authors:
                    prefill['author'] = str(authors[0])
                elif isinstance(authors, str) and authors:
                    prefill['author'] = authors
                if header.get('description'):
                    prefill['description'] = header['description']
        return prefill

    def _start_merge(self):
        """Entry point for the merge process. Validates input and starts worker thread."""
        files = self.merger_tab.get_file_list()
        if not files:
            QMessageBox.warning(self, _tr("msg.no_files", "No Files"),
                                _tr("msg.add_files_first", "Please add pack files first."))
            return

        out_dir = self.merger_tab.entry_output_dir.text().strip()
        if not out_dir or not _os.path.isdir(out_dir):
            QMessageBox.warning(self, _tr("msg.no_output", "No Output"),
                                _tr("msg.select_valid_output", "Please select a valid output directory."))
            return

        self._out_dir = out_dir
        self._files = files
        self._output_format = self.merger_tab.get_output_format()
        self._save_settings()

        # Disable UI during merge
        self.merger_tab.set_merge_running(True)
        self.merger_tab.set_progress(0)
        self.merger_tab.set_status(_tr("status.starting_merge", "Starting merge..."))
        self.mode_label.setText(_tr("status.merging", "Merging..."))

        # Show pack customization dialog if enabled
        if self.customize_pack_after_merge:
            prefill = self._build_customization_prefill(files)
            dlg = PackCustomizationDialog(prefill, self)
            if dlg.exec() == QDialog.Accepted:
                self._pack_customization = dlg.get_customization()
            else:
                self._pack_customization = None
        else:
            self._pack_customization = None

        # Start worker thread
        self.worker_thread = MergeWorkerThread(self, files, out_dir)
        self.worker_thread.progress_update.connect(self._on_merge_progress)
        self.worker_thread.status_update.connect(self._on_merge_status)
        self.worker_thread.finished.connect(self._on_merge_finished)
        self.worker_thread.error.connect(self._on_merge_error)
        self.worker_thread.start()

    def _on_merge_progress(self, value):
        """Update progress bar from worker signal."""
        self.merger_tab.set_progress(value)

    def _on_merge_status(self, text):
        """Update status from worker signal."""
        self.merger_tab.set_status(text)
        self.mode_label.setText(text)

    def _on_merge_finished(self, success, message):
        """Handle merge completion from worker signal."""
        self.merger_tab.set_merge_running(False)
        self.mode_label.setText(_tr("status.ready", "Ready") if success
                                else _tr("status.merge_failed", "Merge failed"))

        if success:
            self.merger_tab.achievement_indicator.set_status_compatible()
            QMessageBox.information(self, _tr("msg.merge_complete", "Merge Complete"), message)
        else:
            self.merger_tab.achievement_indicator.set_status_incompatible()
            QMessageBox.critical(self, _tr("msg.merge_failed", "Merge Failed"), message)

        self.worker_thread = None

    def _on_merge_error(self, error_msg):
        """Handle merge error from worker signal."""
        _logging.error(f"Merge error: {error_msg}")
        self.mode_label.setText(_tr("status.error", "Error"))

    def _cancel_merge(self):
        """Cancel the running merge operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.merger_tab.set_status(_tr("status.cancelling", "Cancelling..."))
            self.mode_label.setText(_tr("status.cancelling_short", "Cancelling"))

    # ──────────────────────────────────────────────────────────────────
    # SETTINGS TAB HANDLERS
    # ──────────────────────────────────────────────────────────────────

    def _settings_browse_output(self):
        """Browse for default output directory in settings tab."""
        path = QFileDialog.getExistingDirectory(
            self, _tr("filedialog.select_default_output", "Select Default Output Directory"))
        if path:
            self.settings_tab.set_output_dir(path)

    def _save_settings_from_tab(self):
        """Save settings from the Settings tab and apply them."""
        new_settings = self.settings_tab.get_settings()
        path = self._get_settings_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(new_settings, f, indent=2)
        except Exception as e:
            _logging.warning(f"Could not save settings: {e}")

        # Apply settings to app state
        new_lang = new_settings.get("lang", self._current_lang)
        if new_lang != self._current_lang:
            self._current_lang = new_lang
            _tr_load(self._current_lang)
            self._retranslate_ui()
        self.modpack_organization = new_settings.get("modpack_organization", False)
        self.merge_by_version = new_settings.get("merge_by_version", False)
        self.customize_pack_after_merge = new_settings.get("customize_pack_after_merge", True)
        self.show_linked_packs_after_merge = new_settings.get("show_linked_packs_after_merge", False)
        out_dir = new_settings.get("output_dir", "")
        if out_dir and _os.path.isdir(out_dir):
            self._out_dir = out_dir
            self.merger_tab.entry_output_dir.setText(out_dir)
        self._settings = new_settings

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — VALIDATION
    # ──────────────────────────────────────────────────────────────────

    def _validate_files(self, show_gui=True):
        """Validate all selected pack files. Returns True if all valid."""
        valid = True
        for file_path in self._files:
            if not _os.path.exists(file_path):
                if show_gui:
                    QMessageBox.critical(self, _tr("msg.file_not_found", "File Not Found"),
                                         _tr("msg.file_not_found_body", "File not found:\n{path}").format(path=file_path))
                return False

            if _os.path.isdir(file_path):
                if not validate_pack_folder(file_path)[0]:
                    if show_gui:
                        QMessageBox.warning(self, _tr("msg.invalid_pack", "Invalid Pack"),
                                            _tr("msg.invalid_pack_body", "Invalid pack folder:\n{path}").format(path=file_path))
                    valid = False
            else:
                ext = _os.path.splitext(file_path)[1].lower()
                if ext not in ('.mcpack', '.mcaddon', '.zip'):
                    if show_gui:
                        QMessageBox.warning(self, _tr("msg.unsupported_file", "Unsupported File"),
                                            _tr("msg.unsupported_file_body", "Unsupported file type:\n{path}").format(path=file_path))
                    valid = False

        return valid

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — VERSION TRACKING
    # ──────────────────────────────────────────────────────────────────

    def _extract_and_store_highest_versions(self):
        """Scan all packs for highest format versions."""
        self.highest_bp_version = [1, 0, 0]
        self.highest_rp_version = [1, 0, 0]
        self.highest_server_version_full = '1.13.0'
        self.highest_server_ui_version_full = '1.2.0'
        self.highest_gametest_version_full = None

        for file_path in self._files:
            manifest = get_pack_manifest_data(file_path)
            if not manifest:
                continue

            # Track format_version
            fmt_ver = manifest.get('format_version', 1)
            if isinstance(fmt_ver, int):
                fmt_list = [fmt_ver, 0, 0]
            elif isinstance(fmt_ver, (list, tuple)):
                fmt_list = list(fmt_ver) + [0, 0, 0]
                fmt_list = fmt_list[:3]
            else:
                fmt_list = [1, 0, 0]

            # Determine if BP or RP
            modules = manifest.get('modules', [])
            for module in modules:
                mtype = module.get('type', '').lower()
                if 'data' in mtype or 'script' in mtype:
                    if fmt_list > self.highest_bp_version:
                        self.highest_bp_version = fmt_list
                elif 'resources' in mtype:
                    if fmt_list > self.highest_rp_version:
                        self.highest_rp_version = fmt_list

            # Track script API versions
            deps = manifest.get('dependencies', [])
            for dep in deps:
                mod_name = dep.get('module_name', '')
                ver = dep.get('version', '1.0.0')
                if isinstance(ver, list):
                    ver_str = '.'.join(str(v) for v in ver)
                else:
                    ver_str = str(ver)

                if mod_name == '@minecraft/server':
                    if self._compare_versions(ver_str, self.highest_server_version_full) > 0:
                        self.highest_server_version_full = ver_str
                elif mod_name == '@minecraft/server-ui':
                    if self._compare_versions(ver_str, self.highest_server_ui_version_full) > 0:
                        self.highest_server_ui_version_full = ver_str
                elif mod_name == '@minecraft/server-gametest':
                    if self.highest_gametest_version_full is None:
                        self.highest_gametest_version_full = ver_str
                    elif self._compare_versions(ver_str, self.highest_gametest_version_full) > 0:
                        self.highest_gametest_version_full = ver_str

    def _compare_versions(self, v1, v2):
        """Compare two version strings. Returns -1, 0, or 1."""
        try:
            v1_parts = [int(x) for x in str(v1).split('.')]
            v2_parts = [int(x) for x in str(v2).split('.')]
            for a, b in zip(v1_parts, v2_parts):
                if a > b:
                    return 1
                elif a < b:
                    return -1
            # Pad shorter version
            if len(v1_parts) > len(v2_parts):
                return 1 if any(v != 0 for v in v1_parts[len(v2_parts):]) else 0
            elif len(v2_parts) > len(v1_parts):
                return -1 if any(v != 0 for v in v2_parts[len(v1_parts):]) else 0
            return 0
        except Exception:
            return 0

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — COMPATIBILITY CHECK
    # ──────────────────────────────────────────────────────────────────

    def _check_compatibility(self, show_gui=True):
        """Check if merged packs will be achievement-compatible."""
        compatible = True
        for file_path in self._files:
            manifest = get_pack_manifest_data(file_path)
            if manifest:
                # Check for script modules — script-based packs disable achievements
                modules = manifest.get('modules', [])
                for module in modules:
                    if module.get('type', '').lower() == 'script':
                        compatible = False
                        break

        if show_gui:
            self.merger_tab.achievement_indicator.set_status(compatible)
        return compatible

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — MAIN PACK PROCESSING
    # ──────────────────────────────────────────────────────────────────

    def _process_packs(self, files, output_dir):
        """
        Main merge pipeline — processes all packs, extracts, categorizes,
        merges JSON, handles entities/items/blocks, and writes output.
        Version grouping (if enabled) is handled by MergeWorkerThread,
        which calls this method once per group with the correct output_dir.
        """
        self._merge_pack_group(files, output_dir)

    def _group_files_by_version(self, files):
        """Group files by their @minecraft/server version."""
        from collections import defaultdict
        groups = defaultdict(list)
        for f in files:
            manifest = get_pack_manifest_data(f)
            ver = "unknown"
            if manifest:
                for dep in manifest.get('dependencies', []):
                    if dep.get('module_name') == '@minecraft/server':
                        v = dep.get('version', 'unknown')
                        ver = '.'.join(str(x) for x in v) if isinstance(v, list) else str(v)
                        break
            groups[ver].append(f)
        return dict(groups)

    def _merge_pack_group(self, files, output_dir):
        """
        Merge a single group of packs into *output_dir*.
        Extracted from _process_packs for version-group reusability.
        """
        output_zip_rp = _os.path.join(output_dir, "resource_pack.zip")
        output_zip_bp = _os.path.join(output_dir, "behavior_pack.zip")

        json_contents_rp = {}
        json_contents_bp = {}
        lang_contents_rp = {}
        lang_contents_bp = {}
        written_paths_rp = set()
        written_paths_bp = set()

        # Entity/player JSON grouping
        player_json_rp = {}
        player_json_bp = {}
        entity_files_rp = {}  # identifier -> {file_path: data}
        entity_files_bp = {}
        item_files_by_id = {}
        block_files_by_id = {}

        # Prepare output dirs
        temp_dir = _os.path.join(output_dir, "temp_merge")
        rp_dir = _os.path.join(temp_dir, "resource_pack")
        bp_dir = _os.path.join(temp_dir, "behavior_pack")
        _os.makedirs(rp_dir, exist_ok=True)
        _os.makedirs(bp_dir, exist_ok=True)

        # ── Identifier conflict scanning ─────────────────────────────
        identifier_manager = None
        try:
            identifier_manager = IdentifierManager()
            all_pack_ids = {}
            for f in files:
                if _os.path.isdir(f):
                    temp_zip = _os.path.join(output_dir, f"_scan_{_os.path.basename(f)}.mcpack")
                    zip_pack_folder(f, temp_zip)
                    scan_path = temp_zip
                else:
                    scan_path = f

                try:
                    with _zipfile.ZipFile(scan_path, 'r') as z:
                        all_pack_ids[f] = identifier_manager.scan_pack_identifiers(z, f)
                except Exception as e:
                    _logging.warning(f"Could not scan identifiers from {f}: {e}")

                if _os.path.isdir(f) and _os.path.isfile(temp_zip):
                    try:
                        _os.remove(temp_zip)
                    except Exception:
                        pass

            if all_pack_ids:
                identifier_manager.detect_conflicts(all_pack_ids)
                conflict_list = identifier_manager.get_conflict_list()
                if conflict_list:
                    # Show conflict resolution dialog (must be in main thread)
                    if _thread_is_main():
                        self._show_conflict_resolution(conflict_list, identifier_manager)
                    else:
                        ev = _threading.Event()

                        def _show_ui():
                            self._show_conflict_resolution(conflict_list, identifier_manager)
                            ev.set()

                        if QApplication.instance():
                            QTimer.singleShot(0, _show_ui)
                            ev.wait(timeout=30)

                identifier_manager.generate_identifier_mappings()
                _logging.info(f"Identifier mappings: {len(identifier_manager.identifier_mapping)} created")
        except Exception as e:
            _logging.warning(f"Identifier manager init failed: {e}")
            identifier_manager = None

        # ── Process each source pack ─────────────────────────────────
        merger = UniversalJsonMerger()
        if _UNIVERSAL_PATCHER:
            merger.set_universal_patcher(_UNIVERSAL_PATCHER)

        for file_idx, file_path in enumerate(files):
            _logging.info(f"Processing [{file_idx + 1}/{len(files)}]: {_os.path.basename(file_path)}")

            # Extract pack
            pack_dirs = []
            if _os.path.isdir(file_path):
                pack_dirs.append(file_path)
            else:
                extract_dir = _tempfile.mkdtemp(prefix='extract_')
                pack_dirs = recursive_extract_pack(file_path, extract_dir)

            for pack_dir in pack_dirs:
                manifest = read_json_safe(_os.path.join(pack_dir, 'manifest.json'))
                if not manifest:
                    continue

                # Determine pack type
                modules = manifest.get('modules', [])
                is_rp = any(m.get('type', '').lower() == 'resources' for m in modules)
                is_bp = any(m.get('type', '').lower() in ('data', 'script') for m in modules)
                if not is_rp and not is_bp:
                    is_bp = True  # Default to BP

                target_dir = rp_dir if is_rp else bp_dir

                # Apply pack-level fixers
                pack_zip = _os.path.join(output_dir, f"_fix_{_os.path.basename(pack_dir)}.mcpack")
                try:
                    zip_pack_folder(pack_dir, pack_zip)
                    with _zipfile.ZipFile(pack_zip, 'r') as z:
                        pack_basename = _os.path.basename(file_path)
                        extra = _apply_pack_fixers(_FIXERS, pack_basename, z)
                        for side, base_dir in [('rp', rp_dir), ('bp', bp_dir)]:
                            for fpath, content in extra.get(side, {}).items():
                                out = _os.path.join(base_dir, fpath)
                                _os.makedirs(_os.path.dirname(out), exist_ok=True)
                                with open(out, 'wb') as f:
                                    f.write(content)
                except Exception:
                    pass
                finally:
                    try:
                        _os.remove(pack_zip)
                    except Exception:
                        pass

                # Walk pack directory
                for root, dirs, files_in_dir in _os.walk(pack_dir):
                    for filename in files_in_dir:
                        filepath = _os.path.join(root, filename)
                        rel_path = _os.path.relpath(filepath, pack_dir)

                        if self.modpack_organization:
                            pack_label = _os.path.splitext(_os.path.basename(file_path))[0]
                            rel_path = _os.path.join(pack_label, rel_path)

                        # Skip manifest (will be regenerated)
                        if _os.path.basename(filepath).lower() == 'manifest.json':
                            continue

                        # Skip pack icon (will be handled separately)
                        if _os.path.basename(filepath).lower().startswith('pack_icon'):
                            continue

                        # Apply ExtendedBE fixers
                        with open(filepath, 'rb') as fh:
                            content_bytes = fh.read()
                        pack_basename = _os.path.basename(file_path)
                        fixed_path, fixed_content = _apply_fixers(
                            _FIXERS, pack_basename, rel_path, content_bytes)
                        if fixed_content is not None:
                            content_bytes = fixed_content

                        # Categorize by extension
                        ext = _os.path.splitext(filename)[1].lower()

                        if ext == '.json':
                            try:
                                text = safe_decode(content_bytes)
                                json_data = _json.loads(text)
                            except Exception:
                                json_data = None

                            if json_data is not None:
                                # Check if mergeable or entity/item/block
                                if filename in _MERGEABLE_FILES:
                                    target = json_contents_rp if is_rp else json_contents_bp
                                    if filename not in target:
                                        target[filename] = []
                                    target[filename].append(json_data)
                                    continue

                                if filename in _LIST_MERGEABLE_FILES:
                                    target = json_contents_rp if is_rp else json_contents_bp
                                    if filename not in target:
                                        target[filename] = []
                                    if isinstance(json_data, list):
                                        target[filename].append(json_data)
                                    continue

                                # Entity files — group by identifier
                                if 'entities/' in rel_path or 'entity/' in rel_path:
                                    identifier = self._get_entity_identifier(json_data)
                                    if identifier:
                                        target_dict = entity_files_rp if is_rp else entity_files_bp
                                        if identifier not in target_dict:
                                            target_dict[identifier] = []
                                        target_dict[identifier].append((rel_path, json_data, file_path))
                                        continue

                                # Item/block files
                                if 'items/' in rel_path:
                                    identifier = self._get_item_identifier(json_data)
                                    if identifier:
                                        if identifier not in item_files_by_id:
                                            item_files_by_id[identifier] = []
                                        item_files_by_id[identifier].append((rel_path, json_data, file_path))
                                        continue

                                if 'blocks/' in rel_path:
                                    identifier = self._get_block_identifier(json_data)
                                    if identifier:
                                        if identifier not in block_files_by_id:
                                            block_files_by_id[identifier] = []
                                        block_files_by_id[identifier].append((rel_path, json_data, file_path))
                                        continue

                                # Player.json handling
                                if filename == 'player.json':
                                    target_dict = player_json_rp if is_rp else player_json_bp
                                    target_dict[rel_path] = json_data
                                    continue

                                # Other JSON — write directly (first-wins for conflicting paths)
                                target_written = written_paths_rp if is_rp else written_paths_bp
                                out_path = _os.path.join(target_dir, rel_path)
                                if rel_path not in target_written:
                                    _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                                    with open(out_path, 'w', encoding='utf-8') as f:
                                        _json.dump(json_data, f, indent=2)
                                    target_written.add(rel_path)

                        elif ext in ('.lang', '.txt'):
                            try:
                                text = safe_decode(content_bytes)
                            except Exception:
                                text = content_bytes.decode('utf-8', errors='replace')
                            target_dict = lang_contents_rp if is_rp else lang_contents_bp
                            if filename not in target_dict:
                                target_dict[filename] = []
                            target_dict[filename].append(text)
                            continue

                        elif ext in ('.js', '.py'):
                            # Script files — write directly (first-wins)
                            target_written = written_paths_bp if is_bp else written_paths_rp
                            out_path = _os.path.join(target_dir, rel_path)
                            if rel_path not in target_written:
                                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                                with open(out_path, 'wb') as f:
                                    f.write(content_bytes)
                                target_written.add(rel_path)

                        else:
                            # Binary / other files — first-wins
                            target_written = written_paths_rp if is_rp else written_paths_bp
                            out_path = _os.path.join(target_dir, rel_path)
                            if rel_path not in target_written:
                                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                                with open(out_path, 'wb') as f:
                                    f.write(content_bytes)
                                target_written.add(rel_path)

        # ── Merge accumulated JSON ────────────────────────────────────
        _logging.info("Merging JSON contents...")

        # Merge entity files
        for identifier, entries in entity_files_rp.items():
            merged = self._merge_entity_group(identifier, entries, merger, identifier_manager)
            if merged:
                out_path = _os.path.join(rp_dir, 'entity', f"{identifier.split(':')[-1]}.entity.json")
                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    _json.dump(merged, f, indent=2)

        for identifier, entries in entity_files_bp.items():
            merged = self._merge_entity_group(identifier, entries, merger, identifier_manager)
            if merged:
                out_path = _os.path.join(bp_dir, 'entities', f"{identifier.split(':')[-1]}.json")
                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    _json.dump(merged, f, indent=2)

        # Merge item files
        for identifier, entries in item_files_by_id.items():
            merged = self._merge_item_group(identifier, entries, merger, identifier_manager)
            if merged:
                out_path = _os.path.join(bp_dir, 'items', f"{identifier.split(':')[-1]}.json")
                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    _json.dump(merged, f, indent=2)

        # Merge block files
        for identifier, entries in block_files_by_id.items():
            merged = self._merge_block_group(identifier, entries, merger, identifier_manager)
            if merged:
                out_path = _os.path.join(bp_dir, 'blocks', f"{identifier.split(':')[-1]}.json")
                _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'w', encoding='utf-8') as f:
                    _json.dump(merged, f, indent=2)

        # Merge mergeable JSON files
        for filename, json_list in json_contents_rp.items():
            merged = merger.merge_json_list(json_list, file_path=filename)
            out_path = _os.path.join(rp_dir, filename)
            _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                _json.dump(merged, f, indent=2)

        for filename, json_list in json_contents_bp.items():
            merged = merger.merge_json_list(json_list, file_path=filename)
            out_path = _os.path.join(bp_dir, filename)
            _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                _json.dump(merged, f, indent=2)

        # Merge list-type JSON files
        for filename, json_lists in json_contents_rp.items():
            if filename in _LIST_MERGEABLE_FILES:
                combined = []
                seen = set()
                for lst in json_lists:
                    if isinstance(lst, list):
                        for item in lst:
                            item_str = str(item)
                            if item_str not in seen:
                                combined.append(item)
                                seen.add(item_str)
                out_path = _os.path.join(rp_dir, filename)
                with open(out_path, 'w', encoding='utf-8') as f:
                    _json.dump(combined, f, indent=2)

        # Merge .lang files
        for filename, texts in lang_contents_rp.items():
            merged = self._merge_lang_texts(texts)
            out_path = _os.path.join(rp_dir, 'texts', filename)
            _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(merged)

        for filename, texts in lang_contents_bp.items():
            merged = self._merge_lang_texts(texts)
            out_path = _os.path.join(bp_dir, 'texts', filename)
            _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(merged)

        # Merge player.json files
        self._merge_player_json(player_json_rp, rp_dir)
        self._merge_player_json(player_json_bp, bp_dir)

        # ── Create output zips ───────────────────────────────────────
        if _os.path.isdir(rp_dir) and _os.listdir(rp_dir):
            zip_pack_folder(rp_dir, output_zip_rp)
            _logging.info(f"Created: {output_zip_rp}")

        if _os.path.isdir(bp_dir) and _os.listdir(bp_dir):
            zip_pack_folder(bp_dir, output_zip_bp)
            _logging.info(f"Created: {output_zip_bp}")

        # Cleanup temp
        try:
            _shutil.rmtree(temp_dir)
        except Exception:
            pass

    def _get_entity_identifier(self, json_data):
        """Extract entity identifier from JSON data."""
        for key in ['minecraft:entity', 'minecraft:client_entity']:
            if key in json_data:
                desc = json_data[key].get('description', {})
                eid = desc.get('identifier')
                if eid:
                    return eid
        return None

    def _get_item_identifier(self, json_data):
        if 'minecraft:item' in json_data:
            return json_data['minecraft:item'].get('description', {}).get('identifier')
        return None

    def _get_block_identifier(self, json_data):
        if 'minecraft:block' in json_data:
            return json_data['minecraft:block'].get('description', {}).get('identifier')
        return None

    def _merge_entity_group(self, identifier, entries, merger, identifier_manager=None):
        """Merge entity files with the same identifier."""
        if not entries:
            return None

        # Honor "Keep one pack" conflict resolution: drop definitions from
        # packs the user did not choose to keep for this identifier.
        if identifier_manager:
            kept = [e for e in entries if identifier_manager.should_include_definition(e[2], identifier)]
            if len(kept) != len(entries):
                _logging.info(f"Conflict resolution for {identifier}: kept {len(kept)}/{len(entries)} definitions")
            entries = kept

        if not entries:
            return None

        # Sort entries by source pack for deterministic order
        entries.sort(key=lambda x: x[0])

        # Use merger for JSON merging
        json_list = [data for _, data, _ in entries]
        merged = merger.merge_json_list(json_list, file_path=f"entity/{identifier}")

        # Update identifiers if manager is active
        if identifier_manager:
            merged = identifier_manager.update_json_identifiers(merged, entries[0][2])

        return merged

    def _merge_item_group(self, identifier, entries, merger, identifier_manager=None):
        if not entries:
            return None
        if identifier_manager:
            kept = [e for e in entries if identifier_manager.should_include_definition(e[2], identifier)]
            if len(kept) != len(entries):
                _logging.info(f"Conflict resolution for {identifier}: kept {len(kept)}/{len(entries)} definitions")
            entries = kept
        if not entries:
            return None
        entries.sort(key=lambda x: x[0])
        json_list = [data for _, data, _ in entries]
        return merger.merge_json_list(json_list, file_path=f"item/{identifier}")

    def _merge_block_group(self, identifier, entries, merger, identifier_manager=None):
        if not entries:
            return None
        if identifier_manager:
            kept = [e for e in entries if identifier_manager.should_include_definition(e[2], identifier)]
            if len(kept) != len(entries):
                _logging.info(f"Conflict resolution for {identifier}: kept {len(kept)}/{len(entries)} definitions")
            entries = kept
        if not entries:
            return None
        entries.sort(key=lambda x: x[0])
        json_list = [data for _, data, _ in entries]
        return merger.merge_json_list(json_list, file_path=f"block/{identifier}")

    def _merge_lang_texts(self, texts):
        """Merge multiple .lang file texts key-by-key. Later values overwrite earlier ones."""
        merged = {}
        for text in texts:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                merged[k.strip()] = v.strip()

        # Reconstruct
        lines = []
        for k, v in merged.items():
            lines.append(f"{k}={v}")
        return '\n'.join(lines)

    def _merge_player_json(self, player_dict, target_dir):
        """Merge player.json files from multiple packs."""
        if not player_dict:
            return

        merger = UniversalJsonMerger()
        merged_data = None

        for rel_path, json_data in player_dict.items():
            if merged_data is None:
                merged_data = json_data
            else:
                merged_data = merger.merge_json_list([merged_data, json_data])

        if merged_data:
            out_path = _os.path.join(target_dir, 'entity', 'player.json')
            _os.makedirs(_os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                _json.dump(merged_data, f, indent=2)

    def _show_conflict_resolution(self, conflict_list, identifier_manager):
        """Show the conflict resolution dialog (must be called from main thread)."""
        dlg = ConflictResolutionDialog(conflict_list, identifier_manager, self)
        dlg.exec()

    # ──────────────────────────────────────────────────────────────────
    # MERGE HELPERS — JSON merging
    # ──────────────────────────────────────────────────────────────────

    _MERGE_MAX_KEYS = frozenset({
        'value', 'max', 'min', 'amount', 'speed', 'damage',
        'range', 'radius', 'duration', 'cooldown', 'max_dist', 'priority',
    })
    _UNION_LIST_KEYS = frozenset({
        'component_groups', 'animations', 'animate', 'particle_effects',
        'sound_effects', 'scripts', 'pools', 'entries', 'conditions',
        'spawn_rules', 'behaviors', 'render_controllers',
    })

    @staticmethod
    def _union_merge_list(existing, incoming):
        """Return existing + items from incoming not already present (by JSON fingerprint)."""
        seen = {_json.dumps(i, sort_keys=True) if isinstance(i, (dict, list)) else str(i)
                for i in existing}
        result = list(existing)
        for item in incoming:
            key = _json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result

    def _merge_json_deep(self, target, source):
        """
        Recursively merge source into target with conflict resolution.
        Dicts recurse, lists union-merge, primitives use max or last-wins.
        """
        for key, value in source.items():
            if key not in target:
                target[key] = value
                continue
            t = target[key]
            if isinstance(t, dict) and isinstance(value, dict):
                self._merge_json_deep(t, value)
            elif isinstance(t, list) and isinstance(value, list):
                target[key] = self._union_merge_list(t, value)
            else:
                if key in ('format_version', 'description', 'identifier'):
                    pass
                elif key in self._MERGE_MAX_KEYS and isinstance(t, (int, float)) and isinstance(value, (int, float)):
                    target[key] = max(t, value)
                else:
                    target[key] = value

    # ──────────────────────────────────────────────────────────────────
    # MERGE PIPELINE — POST-PROCESSING STEPS
    # ──────────────────────────────────────────────────────────────────

    def _delete_manifest_files(self):
        """Remove intermediate manifest files from extracted packs."""
        output_dir = self._out_dir
        for root, dirs, files in _os.walk(output_dir):
            for f in files:
                if f.lower() == 'manifest.json':
                    try:
                        _os.remove(_os.path.join(root, f))
                    except Exception:
                        pass

    def _create_manifest(self):
        """Create unified manifest.json for output packs."""
        output_dir = self._out_dir

        # Behavior pack manifest
        bp_manifest = {
            "format_version": 2,
            "header": {
                "name": "Merged Behavior Pack",
                "description": "Merged by Anvil-MC",
                "uuid": str(_uuid.uuid4()),
                "version": self.highest_bp_version,
                "min_engine_version": [1, 20, 0],
            },
            "modules": [{
                "type": "data",
                "uuid": str(_uuid.uuid4()),
                "version": [1, 0, 0],
            }],
        }

        # Resource pack manifest
        rp_manifest = {
            "format_version": 2,
            "header": {
                "name": "Merged Resource Pack",
                "description": "Merged by Anvil-MC",
                "uuid": str(_uuid.uuid4()),
                "version": self.highest_rp_version,
                "min_engine_version": [1, 20, 0],
            },
            "modules": [{
                "type": "resources",
                "uuid": str(_uuid.uuid4()),
                "version": [1, 0, 0],
            }],
        }

        # Apply customization if available
        if hasattr(self, '_pack_customization') and self._pack_customization:
            cust = self._pack_customization
            bp_manifest['header']['name'] = cust.get('name', 'Merged Behavior Pack')
            bp_manifest['header']['description'] = cust.get('description', '')
            rp_manifest['header']['name'] = cust.get('name', 'Merged Resource Pack')
            rp_manifest['header']['description'] = cust.get('description', '')
            if cust.get('author'):
                author = cust['author'].strip()
                bp_manifest['header']['authors'] = [author]
                rp_manifest['header']['authors'] = [author]

        custom_icon = None
        if hasattr(self, '_pack_customization') and self._pack_customization:
            icon_path = self._pack_customization.get('icon_path')
            if icon_path and _os.path.isfile(icon_path):
                custom_icon = icon_path

        # Write manifests
        bp_zip = _os.path.join(output_dir, "behavior_pack.zip")
        rp_zip = _os.path.join(output_dir, "resource_pack.zip")

        for zip_path, manifest in [(bp_zip, bp_manifest), (rp_zip, rp_manifest)]:
            if _os.path.exists(zip_path):
                temp_dir = _tempfile.mkdtemp(prefix='manifest_')
                try:
                    with _zipfile.ZipFile(zip_path, 'r') as z:
                        z.extractall(temp_dir)
                    m_path = _os.path.join(temp_dir, 'manifest.json')
                    with open(m_path, 'w', encoding='utf-8') as f:
                        _json.dump(manifest, f, indent=2)
                    # Inject custom pack icon if provided
                    if custom_icon:
                        for ext in ('.png', '.jpg', '.jpeg'):
                            old = _os.path.join(temp_dir, f'pack_icon{ext}')
                            if _os.path.isfile(old):
                                try:
                                    _os.remove(old)
                                except Exception:
                                    pass
                        with open(custom_icon, 'rb') as src, \
                                open(_os.path.join(temp_dir, 'pack_icon.png'), 'wb') as dst:
                            dst.write(src.read())
                    # Re-zip
                    zip_pack_folder(temp_dir, zip_path)
                finally:
                    try:
                        _shutil.rmtree(temp_dir)
                    except Exception:
                        pass

    def _merge_json_list_file(self, files, subpath, out_name=None):
        """Merge a JSON list file (e.g. flipbook_textures.json) from multiple packs."""
        merged = []
        for f in files:
            if _os.path.isdir(f):
                p = _os.path.join(f, subpath)
                if _os.path.isfile(p):
                    try:
                        with open(p, 'r', encoding='utf-8') as fh:
                            text = fh.read()
                        cleaned = '\n'.join(ln for ln in text.splitlines() if not ln.strip().startswith('//'))
                        jd = _json.loads(cleaned)
                        if isinstance(jd, list):
                            merged.extend(jd)
                    except Exception:
                        pass
                continue
            try:
                with _zipfile.ZipFile(f, 'r') as z:
                    try:
                        data = z.read(subpath)
                        text = data.decode('latin-1')
                        cleaned = '\n'.join(ln for ln in text.splitlines() if not ln.strip().startswith('//'))
                        jd = _json.loads(cleaned)
                        if isinstance(jd, list):
                            merged.extend(jd)
                    except (KeyError, _json.JSONDecodeError):
                        pass
            except Exception:
                pass

        if merged:
            out = _os.path.join(self._out_dir, out_name or _os.path.basename(subpath))
            with open(out, 'w', encoding='utf-8') as f:
                _json.dump(merged, f)

    def _merge_flipbook_textures(self, files):
        """Merge flipbook_textures.json from multiple packs."""
        self._merge_json_list_file(files, 'textures/flipbook_textures.json')

    def _merge_textures_list(self, files):
        """Merge textures_list.json from multiple packs."""
        self._merge_json_list_file(files, 'textures/textures_list.json')

    def _extract_and_delete_zip_files(self):
        """Extract flipbook/textures_list JSONs from their temp zips and clean up."""
        rp_zip = _os.path.join(self._out_dir, 'resource_pack.zip')
        # If we have standalone flipbook/textures json files, inject them into the RP zip
        for fname in ('flipbook_textures.json', 'textures_list.json'):
            src = _os.path.join(self._out_dir, fname)
            if _os.path.isfile(src) and _os.path.exists(rp_zip):
                try:
                    tmp = _tempfile.mkdtemp(prefix='rp_inject_')
                    with _zipfile.ZipFile(rp_zip, 'r') as z:
                        z.extractall(tmp)
                    dest = _os.path.join(tmp, 'textures', fname)
                    _os.makedirs(_os.path.dirname(dest), exist_ok=True)
                    _shutil.copy2(src, dest)
                    zip_pack_folder(tmp, rp_zip)
                    _shutil.rmtree(tmp)
                except Exception as e:
                    _logging.warning(f"Could not inject {fname} into RP: {e}")
                try:
                    _os.remove(src)
                except Exception:
                    pass

    def _move_to_resource_pack(self):
        """Move textures, flipbook, and textures_list into the resource pack zip."""
        rp_zip = _os.path.join(self._out_dir, 'resource_pack.zip')
        if not _os.path.exists(rp_zip):
            _logging.warning("resource_pack.zip not found — skipping RP finalization")
            return

        try:
            tmp = _tempfile.mkdtemp(prefix='rp_finalize_')
            with _zipfile.ZipFile(rp_zip, 'r') as z:
                z.extractall(tmp)

            # Remove behavior-side files (functions, entities, scripts) from RP
            for folder in ('functions', 'entities', 'scripts'):
                fpath = _os.path.join(tmp, folder)
                if _os.path.isdir(fpath):
                    _shutil.rmtree(fpath)

            # Re-zip
            zip_pack_folder(tmp, rp_zip)
            _shutil.rmtree(tmp)
            _logging.info("Resource pack finalized")
        except Exception as e:
            _logging.warning(f"RP finalization error: {e}")

    def _update_behavior_pack(self):
        """Finalize behavior pack — inject scripts, strip script manifest entries if empty."""
        bp_zip = _os.path.join(self._out_dir, 'behavior_pack.zip')
        scripts_dir = _os.path.join(self._out_dir, 'scripts')

        if not _os.path.exists(bp_zip):
            _logging.warning("behavior_pack.zip not found")
            return

        try:
            tmp = _tempfile.mkdtemp(prefix='bp_finalize_')
            with _zipfile.ZipFile(bp_zip, 'r') as z:
                z.extractall(tmp)

            # Remove old scripts/subpacks from the temp
            for folder in ('scripts', 'subpacks'):
                fpath = _os.path.join(tmp, folder)
                if _os.path.exists(fpath):
                    if _os.path.isdir(fpath):
                        _shutil.rmtree(fpath)
                    else:
                        _os.remove(fpath)

            # Copy new scripts from scripts_dir if they exist
            if _os.path.isdir(scripts_dir):
                _shutil.copytree(scripts_dir, _os.path.join(tmp, 'scripts'), dirs_exist_ok=True)

            # Check if scripts/CodeNex.js has real imports
            codenex = _os.path.join(tmp, 'scripts', 'CodeNex.js')
            has_real_imports = False
            if _os.path.isfile(codenex):
                with open(codenex, 'r', encoding='utf-8', errors='ignore') as f:
                    has_real_imports = any(
                        line.strip().startswith('import ') for line in f
                    )

            if not has_real_imports:
                # Remove empty scripts folder
                sp = _os.path.join(tmp, 'scripts')
                if _os.path.isdir(sp):
                    _shutil.rmtree(sp)
                # Patch manifest to strip script-related entries
                manifest_path = _os.path.join(tmp, 'manifest.json')
                if _os.path.isfile(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        mdata = _json.load(f)
                    mdata['modules'] = [
                        m for m in mdata.get('modules', [])
                        if m.get('type') != 'script'
                    ]
                    caps = mdata.get('capabilities', [])
                    if 'script_eval' in caps:
                        caps.remove('script_eval')
                    script_mods = {'@minecraft/server', '@minecraft/server-ui',
                                   '@minecraft/server-gametest', '@minecraft/server-admin'}
                    mdata['dependencies'] = [
                        d for d in mdata.get('dependencies', [])
                        if d.get('module_name') not in script_mods
                    ]
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        _json.dump(mdata, f, indent=2)
                    _logging.info("Stripped script module from BP manifest (no real imports)")

            # Re-zip
            zip_pack_folder(tmp, bp_zip)
            _shutil.rmtree(tmp)

            # Cleanup scripts dir
            if _os.path.isdir(scripts_dir):
                _shutil.rmtree(scripts_dir)

            _logging.info("Behavior pack finalized")
        except Exception as e:
            _logging.warning(f"BP finalization error: {e}")

    def _move_tick_and_delete_functions(self):
        """Handle tick.json — merge tick functions from all packs."""
        # tick.json contains function paths to run each tick
        out_dir = self._out_dir
        rp_zip = _os.path.join(out_dir, 'resource_pack.zip')
        bp_zip = _os.path.join(out_dir, 'behavior_pack.zip')

        # Scan all source packs for tick.json and merge
        all_tick_data = []
        for f in self._files:
            try:
                data = None
                if _os.path.isdir(f):
                    tick_path = _os.path.join(f, 'tick.json')
                    if _os.path.isfile(tick_path):
                        with open(tick_path, 'r', encoding='utf-8', errors='ignore') as fh:
                            data = _json.loads(fh.read())
                else:
                    with _zipfile.ZipFile(f, 'r') as z:
                        try:
                            data = _json.loads(z.read('tick.json').decode('utf-8'))
                        except (KeyError, _json.JSONDecodeError):
                            pass
                if isinstance(data, dict):
                    all_tick_data.append(data)
            except Exception:
                pass

        if all_tick_data and _os.path.exists(bp_zip):
            # Merge tick.json values
            merged = {}
            for td in all_tick_data:
                for k, v in td.items():
                    if k not in merged:
                        merged[k] = v
                    elif isinstance(merged[k], list) and isinstance(v, list):
                        merged[k] = list(set(merged[k] + v))
            # Write into BP
            try:
                tmp = _tempfile.mkdtemp(prefix='tick_')
                with _zipfile.ZipFile(bp_zip, 'r') as z:
                    z.extractall(tmp)
                with open(_os.path.join(tmp, 'tick.json'), 'w', encoding='utf-8') as f:
                    _json.dump(merged, f, indent=2)
                zip_pack_folder(tmp, bp_zip)
                _shutil.rmtree(tmp)
            except Exception as e:
                _logging.warning(f"tick.json merge error: {e}")

    def _process_script_files(self, files):
        """Process and concatenate script files from all packs into scripts/CodeNex.js."""
        out_dir = self._out_dir
        scripts_dir = _os.path.join(out_dir, 'scripts')
        _os.makedirs(scripts_dir, exist_ok=True)

        all_scripts = []
        seen_imports = set()
        seen_code = set()

        for f in files:
            try:
                if _os.path.isdir(f):
                    names = []
                    for root, dirs, fnames in _os.walk(f):
                        for fn in fnames:
                            rel = _os.path.relpath(_os.path.join(root, fn), f)
                            names.append(rel)
                else:
                    with _zipfile.ZipFile(f, 'r') as z:
                        names = z.namelist()

                for name in names:
                    if name.startswith('scripts/') and name.endswith('.js'):
                        try:
                            if _os.path.isdir(f):
                                with open(_os.path.join(f, name), 'r', encoding='utf-8', errors='ignore') as fh:
                                    content = fh.read()
                            else:
                                with _zipfile.ZipFile(f, 'r') as z:
                                    content = z.read(name).decode('utf-8', errors='ignore')

                            lines = content.splitlines()
                            imports = [ln for ln in lines if ln.strip().startswith('import ')]
                            code = [ln for ln in lines if not ln.strip().startswith('import ')]

                            for imp in imports:
                                if imp not in seen_imports:
                                    seen_imports.add(imp)
                                    all_scripts.append(imp)

                            for cl in code:
                                stripped = cl.strip()
                                if stripped and stripped not in seen_code:
                                    seen_code.add(stripped)
                                    all_scripts.append(cl)
                        except Exception:
                            pass
            except Exception:
                pass

        if all_scripts:
            codenex_path = _os.path.join(scripts_dir, 'CodeNex.js')
            with open(codenex_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_scripts))
            _logging.info(f"Created CodeNex.js with {len(all_scripts)} lines from {len(files)} pack(s)")

    def _move_and_cleanup(self):
        """Move files between output zips and clean up intermediate state."""
        pass  # Handled by _update_behavior_pack and _move_to_resource_pack

    def _final_cleanup(self):
        """Final cleanup of temporary files (preserves output zips)."""
        out_dir = self._out_dir
        # Remove temp_merge directory if present
        temp_merge = _os.path.join(out_dir, 'temp_merge')
        if _os.path.isdir(temp_merge):
            try:
                _shutil.rmtree(temp_merge)
            except Exception:
                pass
        # Remove any temp scan/extract dirs
        for fname in _os.listdir(out_dir):
            if fname.startswith('temp_scan_') or fname.startswith('extract_') or fname.startswith('temp_'):
                try:
                    path = _os.path.join(out_dir, fname)
                    if _os.path.isdir(path):
                        _shutil.rmtree(path)
                    else:
                        _os.remove(path)
                except Exception:
                    pass

    def _package_output(self):
        """Convert intermediate resource_pack.zip / behavior_pack.zip into the
        user-selected output format (mcaddon / mcpack / zip)."""
        out_dir = self._out_dir
        fmt = getattr(self, '_output_format', 'mcaddon')
        rp_zip = _os.path.join(out_dir, 'resource_pack.zip')
        bp_zip = _os.path.join(out_dir, 'behavior_pack.zip')

        if fmt == 'zip':
            _logging.info("Output format: .zip (no repackaging)")
            return

        if fmt == 'mcpack':
            # Rename to .mcpack extension
            for src in (rp_zip, bp_zip):
                if not _os.path.isfile(src):
                    continue
                dst = src[:-4] + '.mcpack'
                if _os.path.exists(dst):
                    _os.remove(dst)
                _os.rename(src, dst)
                _logging.info(f"Created {_os.path.basename(dst)}")
            return

        # fmt == 'mcaddon' — combine both packs into a single .mcaddon
        # An .mcaddon is a zip containing pack folders, each with its own
        # manifest.json.  Minecraft imports all packs when opened.
        mcaddon_path = _os.path.join(out_dir, 'AnvilMC_merged.mcaddon')
        tmp = _tempfile.mkdtemp(prefix='mcaddon_')
        try:
            # Extract each pack into its own subfolder
            if _os.path.isfile(rp_zip):
                rp_dir = _os.path.join(tmp, 'resource_pack')
                _os.makedirs(rp_dir, exist_ok=True)
                with _zipfile.ZipFile(rp_zip, 'r') as z:
                    z.extractall(rp_dir)
                _os.remove(rp_zip)
            if _os.path.isfile(bp_zip):
                bp_dir = _os.path.join(tmp, 'behavior_pack')
                _os.makedirs(bp_dir, exist_ok=True)
                with _zipfile.ZipFile(bp_zip, 'r') as z:
                    z.extractall(bp_dir)
                _os.remove(bp_zip)

            zip_pack_folder(tmp, mcaddon_path)
            _logging.info(f"Created {_os.path.basename(mcaddon_path)} "
                          f"(RP+BP combined)")
        except Exception as e:
            _logging.error(f"Failed to create .mcaddon: {e}")
        finally:
            if _os.path.isdir(tmp):
                try:
                    _shutil.rmtree(tmp)
                except Exception:
                    pass

    # ──────────────────────────────────────────────────────────────────
    # MCPACKER TAB
    # ──────────────────────────────────────────────────────────────────

    def _mcpacker_add(self):
        """Add folders to the MCPacker tab."""
        folder = QFileDialog.getExistingDirectory(
            self, _tr("filedialog.select_pack_folder", "Select Pack Folder"))
        if folder:
            items = []
            for i in range(self.mcpacker_tab.file_list.count()):
                items.append(self.mcpacker_tab.file_list.item(i).text())
            if folder not in items:
                self.mcpacker_tab.file_list.addItem(folder)

    def _mcpacker_remove(self):
        """Remove selected items from MCPacker tab."""
        selected = self.mcpacker_tab.file_list.selectedItems()
        for item in selected:
            self.mcpacker_tab.file_list.takeItem(self.mcpacker_tab.file_list.row(item))

    def _mcpacker_browse_output(self):
        """Browse for MCPacker output file."""
        path, _ = QFileDialog.getSaveFileName(
            self, _tr("filedialog.save_mcpack_as", "Save MCPack As"), "",
            _tr("filedialog.mcpack_filter", "MCPack Files (*.mcpack)"))
        if path:
            self.mcpacker_tab.output_path.setText(path)

    def _mcpacker_start(self):
        """Start the MCPacker operation."""
        mode = "pack" if self.mcpacker_tab.mode_combo.currentData() == "pack" else "unpack"
        items = []
        for i in range(self.mcpacker_tab.file_list.count()):
            items.append(self.mcpacker_tab.file_list.item(i).text())

        if not items:
            QMessageBox.warning(self, _tr("msg.no_items", "No Items"),
                                _tr("msg.add_folders_first", "Please add folders first."))
            return

        output = self.mcpacker_tab.output_path.text().strip()
        if not output:
            QMessageBox.warning(self, _tr("msg.no_output", "No Output"),
                                _tr("msg.specify_output_path", "Please specify an output path."))
            return

        if mode == "pack":
            for folder in items:
                if _os.path.isdir(folder):
                    out_name = _os.path.basename(folder.rstrip('/\\')) + '.mcpack'
                    out_path = _os.path.join(output, out_name) if _os.path.isdir(output) else output
                    folder_to_mcpack(folder, out_path)
            self.mcpacker_tab.set_status(_tr("status.packing_complete", "Packing complete!"))
        else:
            for archive in items:
                if _os.path.isfile(archive):
                    out_dir = output if _os.path.isdir(output) else _os.path.dirname(output)
                    recursive_extract_pack(archive, out_dir)
            self.mcpacker_tab.set_status(_tr("status.unpacking_complete", "Unpacking complete!"))

    # ──────────────────────────────────────────────────────────────────
    # LIST MAKER TAB
    # ──────────────────────────────────────────────────────────────────

    def _list_maker_add(self):
        """Add files to the List Maker tab."""
        files, _ = QFileDialog.getOpenFileNames(
            self, _tr("filedialog.select_pack_files", "Select Pack Files"), "",
            _tr("filedialog.pack_filter_short", "Minecraft Packs (*.mcpack *.mcaddon *.zip)"))
        for f in files:
            timestamp = _datetime.datetime.fromtimestamp(_os.path.getmtime(f))
            item = QTreeWidgetItem([_os.path.basename(f), _tr("common.pack", "Pack"),
                                    timestamp.strftime("%Y-%m-%d %H:%M")])
            self.list_maker_tab.file_tree.addTopLevelItem(item)

    def _list_maker_clear(self):
        """Clear the list maker tree."""
        self.list_maker_tab.clear_tree()

    def _list_maker_organize(self):
        """Organize items in the list maker by date."""
        tree = self.list_maker_tab.file_tree
        # Collect all items
        items = []
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item:
                items.append((item.text(2), item))

        # Sort by date (descending)
        items.sort(key=lambda x: x[0], reverse=True)

        tree.clear()
        for _, item in items:
            tree.addTopLevelItem(item)

        self.list_maker_tab.set_status(_tr("status.organized_n_items", "Organized {n} items by date").format(n=len(items)))

    def _list_maker_export(self):
        """Export the list maker data to a file."""
        path, _ = QFileDialog.getSaveFileName(
            self, _tr("filedialog.export_list", "Export List"), "",
            _tr("filedialog.export_filter", "Text Files (*.txt);;CSV Files (*.csv)"))
        if not path:
            return

        tree = self.list_maker_tab.file_tree
        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = _csv.writer(f)
                writer.writerow([_tr("list_maker.col.filename", "Filename"),
                                 _tr("common.type", "Type"),
                                 _tr("list_maker.col.date_modified", "Date Modified")])
                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    if item:
                        writer.writerow([item.text(0), item.text(1), item.text(2)])
            self.list_maker_tab.set_status(
                _tr("status.exported_to", "Exported to {name}").format(name=_os.path.basename(path)))
        except Exception as e:
            QMessageBox.critical(self, _tr("msg.export_error", "Export Error"),
                                 _tr("msg.export_failed", "Failed to export: {error}").format(error=e))

    # ──────────────────────────────────────────────────────────────────
    # HELP / ABOUT
    # ──────────────────────────────────────────────────────────────────

    def _show_help(self):
        """Switch to the help tab."""
        self.notebook.setCurrentWidget(self.help_tab)

    def _show_about(self):
        """Show the About dialog."""
        dlg = AboutDialog(self)
        dlg.exec()

    # ──────────────────────────────────────────────────────────────────
    # WINDOW CLOSE
    # ──────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        """Handle window close — clean up worker threads."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait(5000)
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────

def _apply_fixers(fixers, pack_basename, filepath, content_bytes):
    """Apply ExtendedBE per-file fixers to a single file."""
    for mod in fixers:
        targets = getattr(mod, 'TARGETS', [])
        if not any(_fnmatch.fnmatch(pack_basename, pat) for pat in targets):
            continue
        fix_fn = getattr(mod, 'fix', None)
        if not callable(fix_fn):
            continue
        try:
            result = fix_fn(pack_basename, filepath, content_bytes)
            if result is None:
                continue
            if isinstance(result, tuple):
                new_path, new_bytes = result
                if new_path is not None:
                    filepath = new_path
                if new_bytes is not None:
                    content_bytes = new_bytes
            else:
                content_bytes = result
        except Exception as e:
            _logging.warning(f"[Fixer] Error in {getattr(mod, 'DESCRIPTION', mod.__name__)}: {e}")
    return filepath, content_bytes


def _apply_pack_fixers(fixers, pack_basename, zip_file):
    """Run pack-level fixers that need to scan the full pack (e.g. missing definitions)."""
    rp_extra, bp_extra = {}, {}
    for mod in fixers:
        targets = getattr(mod, 'TARGETS', [])
        if not any(_fnmatch.fnmatch(pack_basename, pat) for pat in targets):
            continue
        fix_pack_fn = getattr(mod, 'fix_pack', None)
        if not callable(fix_pack_fn):
            continue
        try:
            result = fix_pack_fn(pack_basename, zip_file) or {}
            rp_extra.update(result.get('rp', {}))
            bp_extra.update(result.get('bp', {}))
        except Exception as e:
            _logging.warning(f"[Fixer] Error in pack fixer '{getattr(mod, 'DESCRIPTION', mod.__name__)}': {e}")
    return {'rp': rp_extra, 'bp': bp_extra}


def _thread_is_main():
    """Return True if called from the main thread."""
    return _threading.current_thread() is _threading.main_thread()
