"""
Custom dialogs for Anvil-MC.
Includes conflict resolution, subpack selection, version check, pack customization, and about dialogs.
"""
import os
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox,
    QTextEdit, QLineEdit, QFileDialog, QApplication, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from src.app import APP_VERSION
from src.core.i18n import _tr


class ConflictResolutionDialog(QDialog):
    """
    Dialog for resolving identifier conflicts during pack merging.
    Shows a list of conflicting identifiers and allows the user to choose
    which pack's definition to keep, or keep all (deep-merge).
    """

    def __init__(self, conflict_list, identifier_manager, parent=None):
        super().__init__(parent)
        self.conflict_list = conflict_list
        self.identifier_manager = identifier_manager
        self.setWindowTitle(_tr("conflict.window_title", "Resolve Identifier Conflicts"))
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(
            f"<b>{_tr('conflict.count_detected', '{n} identifier conflict(s) detected.').format(n=len(self.conflict_list))}</b><br>"
            + _tr("conflict.desc", "Choose which pack's definition to keep, or keep all for deep-merge."))
        header.setWordWrap(True)
        header.setStyleSheet("color: #C6C6C6; font-size: 11pt; padding: 8px;")
        layout.addWidget(header)

        # Scroll area for conflicts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 2px solid #3D3D3D; background-color: #252525;")

        scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(scroll_content)
        self._scroll_layout.setContentsMargins(8, 8, 8, 8)
        self._scroll_layout.setSpacing(6)

        self._conflict_widgets = {}  # identifier -> (group_box, button_group, radio_buttons)

        for identifier, pack_paths in self.conflict_list:
            group = QGroupBox(identifier)
            group.setStyleSheet("QGroupBox { color: #FFAA00; font-weight: bold; border: 2px solid #3D3D3D; margin-top: 12px; } "
                                "QGroupBox::title { color: #FFAA00; }")
            g_layout = QVBoxLayout(group)

            btn_group = QButtonGroup(group)

            # "Keep all (deep merge)" option
            rb_keep_all = QRadioButton(_tr("conflict.keep_all_deep", "Keep all (deep merge)"))
            rb_keep_all.setChecked(True)
            rb_keep_all.setStyleSheet("color: #55FF55;")
            btn_group.addButton(rb_keep_all, -1)
            g_layout.addWidget(rb_keep_all)

            radios = {None: rb_keep_all}

            for pack_path in pack_paths:
                pack_name = os.path.basename(pack_path)
                rb = QRadioButton(_tr("conflict.keep", "Keep: {name}").format(name=pack_name))
                rb.setStyleSheet("color: #C6C6C6;")
                btn_group.addButton(rb)
                g_layout.addWidget(rb)
                radios[pack_path] = rb

            self._conflict_widgets[identifier] = (group, btn_group, radios)
            self._scroll_layout.addWidget(group)

        self._scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_select_all = QPushButton(_tr("conflict.keep_all_all", "Keep All (All)"))
        self._btn_select_all.setProperty("class", "adco")
        self._btn_select_all.clicked.connect(self._select_all_keep_all)
        btn_layout.addWidget(self._btn_select_all)

        self._btn_ok = QPushButton(_tr("conflict.apply_resolutions", "Apply Resolutions"))
        self._btn_ok.setProperty("class", "primary")
        self._btn_ok.clicked.connect(self._apply)
        btn_layout.addWidget(self._btn_ok)

        self._btn_cancel = QPushButton(_tr("conflict.cancel_merge", "Cancel Merge"))
        self._btn_cancel.setProperty("class", "danger")
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        layout.addLayout(btn_layout)

    def _select_all_keep_all(self):
        """Set all conflicts to 'keep all'."""
        for identifier, (_, _, radios) in self._conflict_widgets.items():
            radios[None].setChecked(True)

    def _apply(self):
        """Apply the user's conflict resolution choices."""
        for identifier, (_, btn_group, radios) in self._conflict_widgets.items():
            selected_id = btn_group.checkedId()
            if selected_id == -1:
                self.identifier_manager.set_user_resolution(identifier, None)
            else:
                pack_paths = [p for p in radios if p is not None]
                idx = -selected_id - 2
                if 0 <= idx < len(pack_paths):
                    self.identifier_manager.set_user_resolution(identifier, pack_paths[idx])

        self.identifier_manager.generate_identifier_mappings()
        self.accept()


class VersionCheckDialog(QDialog):
    """
    Read-only overview of loaded packs grouped by their @minecraft/server
    Script API version. Provides live search, expand/collapse, and a
    copy-to-clipboard report.
    """

    def __init__(self, version_groups, failed=0, parent=None):
        super().__init__(parent)
        self._raw_groups = version_groups or {}
        self._failed = failed
        self.merge_by_version_requested = False
        self.setWindowTitle(_tr("version_check.window_title", "Pack Version Check"))
        self.setMinimumSize(620, 480)
        self.setModal(True)
        self._ordered = self._ordered_groups()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QLabel(_tr("version_check.header",
                            "Packs grouped by their @minecraft/server Script API version."))
        header.setWordWrap(True)
        header.setStyleSheet("color: #C6C6C6; font-size: 11pt; font-weight: 600;")
        layout.addWidget(header)

        # Stats
        total = sum(len(p) for p in self._raw_groups.values())
        n_versions = len([v for v in self._raw_groups if v != "No Script API"])
        with_scripts = sum(len(p) for v, p in self._raw_groups.items() if v != "No Script API")
        without_scripts = total - with_scripts

        stats = QLabel(
            _tr("version_check.stats",
                "Total: <b>{total}</b> pack(s) &nbsp;•&nbsp; "
                "<b>{versions}</b> script API version(s) &nbsp;•&nbsp; "
                "<b>{with}</b> with scripts &nbsp;•&nbsp; "
                "<b>{without}</b> without")
            .format_map({"total": total, "versions": n_versions,
                         "with": with_scripts, "without": without_scripts})
        )
        stats.setStyleSheet("color: #C6C6C6;")
        layout.addWidget(stats)

        # Warnings
        if self._failed:
            w = QLabel(_tr("version_check.manifests_failed",
                           "⚠ Could not read {n} manifest(s).").format(n=self._failed))
            w.setStyleSheet("color: #FF9F3C;")
            layout.addWidget(w)

        if n_versions > 1:
            warn_row = QHBoxLayout()
            w = QLabel(_tr("version_check.multi_version_warning",
                "⚠ Multiple @minecraft/server versions detected — "
                "script packs target different API versions and may not be cross-compatible."))
            w.setWordWrap(True)
            w.setStyleSheet("color: #FF9F3C;")
            warn_row.addWidget(w, 1)

            btn_mvb = QPushButton(_tr("version_check.enable_merge_by_version", "Enable Merge by Version"))
            btn_mvb.setProperty("class", "primary")
            btn_mvb.setToolTip(_tr("version_check.enable_merge_by_version_tip",
                "Switch the merge to split output by @minecraft/server version."))
            btn_mvb.clicked.connect(self._request_merge_by_version)
            warn_row.addWidget(btn_mvb)
            layout.addLayout(warn_row)

        # Search + toolbar
        tool_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText(_tr("version_check.filter_placeholder", "Filter packs by name..."))
        self._search.textChanged.connect(self._rebuild)
        tool_row.addWidget(self._search, 1)

        btn_expand = QPushButton(_tr("common.expand_all", "Expand All"))
        btn_expand.setProperty("class", "adco")
        btn_expand.clicked.connect(lambda: self._set_expanded(True))
        tool_row.addWidget(btn_expand)

        btn_collapse = QPushButton(_tr("common.collapse_all", "Collapse All"))
        btn_collapse.setProperty("class", "adco")
        btn_collapse.clicked.connect(lambda: self._set_expanded(False))
        tool_row.addWidget(btn_collapse)

        btn_copy = QPushButton(_tr("common.copy", "Copy"))
        btn_copy.setProperty("class", "adco")
        btn_copy.clicked.connect(self._copy_report)
        tool_row.addWidget(btn_copy)
        layout.addLayout(tool_row)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([
            _tr("common.pack", "Pack"),
            _tr("common.type", "Type"),
        ])
        self._tree.setRootIsDecorated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setStyleSheet(
            "QTreeWidget { background-color: #252525; color: #C6C6C6; "
            "border: 3px solid #3D3D3D; } "
            "QTreeWidget::item:selected { background-color: #7CBD4D; color: #FFFFFF; } "
            "QTreeWidget::item { padding: 4px; } "
            "QHeaderView::section { background-color: #3D3D3D; color: #C6C6C6; "
            "border: none; padding: 6px; font-weight: 600; }"
        )
        tree_header = self._tree.header()
        tree_header.setStretchLastSection(False)
        tree_header.setSectionResizeMode(0, QHeaderView.Stretch)
        tree_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self._tree, 1)

        self._rebuild("")

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton(_tr("common.close", "Close"))
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _version_key(v):
        """Sort real versions newest-first; 'No Script API' sorts last."""
        if v == "No Script API":
            return (1, ())
        parts = []
        for p in re.split(r'[.\-]', str(v)):
            m = re.match(r'(\d+)', p)
            parts.append(int(m.group(1)) if m else 0)
        return (0, tuple(parts))

    def _ordered_groups(self):
        real = [(v, p) for v, p in self._raw_groups.items() if v != "No Script API"]
        none = [(v, p) for v, p in self._raw_groups.items() if v == "No Script API"]
        real.sort(key=lambda kv: self._version_key(kv[0])[1], reverse=True)
        return real + none

    def _request_merge_by_version(self):
        """User asked to enable merge-by-version from the suggestion; close the dialog."""
        self.merge_by_version_requested = True
        self.accept()

    def _rebuild(self, filter_text=""):
        self._tree.clear()
        f = filter_text.strip().lower()

        for version, packs in self._ordered:
            visible = [p for p in packs if (not f) or (f in p.get('name', '').lower())]
            if not visible:
                continue

            version_item = QTreeWidgetItem([f"{version}   ({len(visible)})", ""])
            version_item.setExpanded(True)
            font = version_item.font(0)
            font.setBold(True)
            version_item.setFont(0, font)
            version_item.setForeground(0, QColor("#7CBD4D"))

            for pack_info in visible:
                child = QTreeWidgetItem([
                    pack_info.get('name', 'Unknown'),
                    pack_info.get('type', ''),
                ])
                scripts = pack_info.get('scripts', [])
                if scripts:
                    child.setToolTip(0, "\n".join(scripts))
                version_item.addChild(child)

            self._tree.addTopLevelItem(version_item)

    def _set_expanded(self, expanded):
        for i in range(self._tree.topLevelItemCount()):
            self._tree.topLevelItem(i).setExpanded(expanded)

    def _copy_report(self):
        total = sum(len(p) for p in self._raw_groups.values())
        n_versions = len([v for v in self._raw_groups if v != "No Script API"])
        lines = [f"Pack Version Check — {total} pack(s), {n_versions} script API version(s)"]
        for version, packs in self._ordered:
            lines.append("")
            lines.append(f"{version} ({len(packs)}):")
            for p in packs:
                t = p.get('type', '')
                suffix = f" [{t}]" if t else ""
                lines.append(f"  - {p.get('name', 'Unknown')}{suffix}")
        QApplication.clipboard().setText("\n".join(lines))


class PackCustomizationDialog(QDialog):
    """
    Dialog for customizing the merged pack's name, description, author, and icon.
    Optional *prefill* dict (name/author/description) seeds the fields, typically
    from the first selected pack's manifest.
    """

    def __init__(self, prefill=None, parent=None, show_script_entry=False):
        super().__init__(parent)
        self._prefill = prefill or {}
        self._custom_icon_path = None
        self._show_script_entry = show_script_entry
        self.setWindowTitle(_tr("customize.window_title", "Customize Merged Pack"))
        self.setMinimumSize(560, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Pack name
        self._name_edit = QLineEdit(self._prefill.get('name', _tr("customize.default_name", "Merged Pack")))
        form.addRow(_tr("customize.name", "Pack Name:"), self._name_edit)

        # Description
        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(72)
        self._desc_edit.setPlainText(
            self._prefill.get('description', _tr("customize.default_desc", "Merged behavior and resource pack")))
        form.addRow(_tr("customize.description", "Description:"), self._desc_edit)

        # Author
        self._author_edit = QLineEdit(self._prefill.get('author', "Anvil-MC"))
        form.addRow(_tr("customize.author", "Author:"), self._author_edit)

        # Script entry name — only shown when enabled in settings
        if self._show_script_entry:
            self._script_entry_edit = QLineEdit(
                self._prefill.get('script_entry_name', 'main.js'))
            self._script_entry_edit.setPlaceholderText("main.js")
            form.addRow(_tr("customize.script_entry", "Script Entry:"), self._script_entry_edit)

        layout.addLayout(form)

        # Pack icon row with preview
        icon_row = QHBoxLayout()
        self._icon_preview = QLabel(_tr("customize.no_icon_short", "none"))
        self._icon_preview.setFixedSize(48, 48)
        self._icon_preview.setAlignment(Qt.AlignCenter)
        self._icon_preview.setStyleSheet(
            "QLabel { background-color: #252525; border: 2px solid #3D3D3D; "
            "color: #606060; font-size: 9pt; }")
        icon_row.addWidget(self._icon_preview)

        icon_controls = QVBoxLayout()
        icon_controls.setSpacing(4)
        self._icon_path_label = QLabel(_tr("customize.no_icon",
            "No icon selected (will use first pack's icon)"))
        self._icon_path_label.setStyleSheet("color: #888888;")
        icon_controls.addWidget(self._icon_path_label)
        icon_btn_row = QHBoxLayout()
        browse_btn = QPushButton(_tr("common.browse", "Browse..."))
        browse_btn.clicked.connect(self._browse_icon)
        clear_btn = QPushButton(_tr("common.clear", "Clear"))
        clear_btn.clicked.connect(self._clear_icon)
        icon_btn_row.addWidget(browse_btn)
        icon_btn_row.addWidget(clear_btn)
        icon_btn_row.addStretch()
        icon_controls.addLayout(icon_btn_row)
        icon_row.addLayout(icon_controls, 1)

        icon_group = QGroupBox(_tr("customize.icon", "Pack Icon (optional)"))
        icon_group_layout = QVBoxLayout(icon_group)
        icon_group_layout.setContentsMargins(10, 8, 10, 8)
        icon_group_layout.addLayout(icon_row)
        layout.addWidget(icon_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton(_tr("customize.apply", "Apply"))
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(_tr("customize.skip", "Skip"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, _tr("customize.pick_icon", "Select Pack Icon"), "",
            _tr("customize.images_filter", "Images (*.png *.jpg *.jpeg)"))
        if path:
            self._custom_icon_path = path
            self._icon_path_label.setText(os.path.basename(path))
            pix = QPixmap(path)
            if not pix.isNull():
                self._icon_preview.setPixmap(
                    pix.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._icon_preview.setText("")

    def _clear_icon(self):
        self._custom_icon_path = None
        self._icon_path_label.setText(_tr("customize.no_icon",
            "No icon selected (will use first pack's icon)"))
        self._icon_preview.clear()
        self._icon_preview.setText(_tr("customize.no_icon_short", "none"))

    def get_customization(self):
        """Return dict with name, description, author, script entry, and optional icon path."""
        script_name = 'main.js'
        if self._show_script_entry:
            script_name = self._script_entry_edit.text().strip() or 'main.js'
            if not script_name.endswith('.js'):
                script_name += '.js'
        return {
            'name': self._name_edit.text().strip() or "Merged Pack",
            'description': self._desc_edit.toPlainText().strip(),
            'author': self._author_edit.text().strip() or "Anvil-MC",
            'script_entry_name': script_name,
            'icon_path': self._custom_icon_path,
        }


class AboutDialog(QDialog):
    """About dialog showing application info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_tr("about.window_title", "About Anvil-MC"))
        self.setFixedSize(420, 320)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Anvil-MC")
        title.setStyleSheet("color: #7CBD4D; font-size: 24pt; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(_tr("about.subtitle", "Minecraft Bedrock Edition Addon Merger"))
        subtitle.setStyleSheet("color: #C6C6C6; font-size: 11pt;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        version = QLabel(_tr("about.version", "Version {ver}").format(ver=APP_VERSION))
        version.setStyleSheet("color: #888888; font-size: 10pt;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(16)

        desc = QLabel(_tr("about.description",
            "A fully local tool for merging Minecraft Bedrock Edition\n"
            "addon packs with intelligent conflict resolution,\n"
            "subpack selection, and automated compatibility fixes."))
        desc.setStyleSheet("color: #B0B0B0; font-size: 10pt;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(16)

        footer = QLabel(_tr("about.footer", "Built with PySide6  |  Auto Fixer Framework"))
        footer.setStyleSheet("color: #606060; font-size: 9pt;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()

        ok_btn = QPushButton(_tr("common.close", "Close"))
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(120)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
