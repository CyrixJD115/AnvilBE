"""
Custom dialogs for Anvil-MC.
Includes conflict resolution, subpack selection, version check, pack customization, and about dialogs.
"""
import os as _os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup, QGroupBox, QCheckBox,
    QTextEdit, QLineEdit, QFileDialog, QMessageBox, QDialogButtonBox,
    QTreeWidget, QTreeWidgetItem, QScrollArea, QWidget, QGridLayout,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap


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
        self.setWindowTitle("Resolve Identifier Conflicts")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(
            f"<b>{len(self.conflict_list)} identifier conflict(s) detected.</b><br>"
            "Choose which pack's definition to keep, or keep all for deep-merge.")
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
            rb_keep_all = QRadioButton("Keep all (deep merge)")
            rb_keep_all.setChecked(True)
            rb_keep_all.setStyleSheet("color: #55FF55;")
            btn_group.addButton(rb_keep_all, -1)
            g_layout.addWidget(rb_keep_all)

            radios = {None: rb_keep_all}

            for pack_path in pack_paths:
                pack_name = _os.path.basename(pack_path)
                rb = QRadioButton(f"Keep: {pack_name}")
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

        self._btn_select_all = QPushButton("Keep All (All)")
        self._btn_select_all.setProperty("class", "adco")
        self._btn_select_all.clicked.connect(self._select_all_keep_all)
        btn_layout.addWidget(self._btn_select_all)

        self._btn_ok = QPushButton("Apply Resolutions")
        self._btn_ok.setProperty("class", "primary")
        self._btn_ok.clicked.connect(self._apply)
        btn_layout.addWidget(self._btn_ok)

        self._btn_cancel = QPushButton("Cancel Merge")
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


class SubpackSelectionDialog(QDialog):
    """
    Dialog for selecting subpack variants when packs contain subpack options.
    """

    def __init__(self, pack_subpack_map, parent=None):
        """
        *pack_subpack_map*: dict of pack_name -> list of (subpack_name, subpack_path)
        """
        super().__init__(parent)
        self.pack_subpack_map = pack_subpack_map
        self.selections = {}
        self.setWindowTitle("Select Subpack Variants")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Select which subpack variant to use for each pack:")
        header.setWordWrap(True)
        header.setStyleSheet("color: #C6C6C6; font-size: 11pt;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 2px solid #3D3D3D; background-color: #252525;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setSpacing(8)

        self._groups = {}

        for pack_name, subpacks in self.pack_subpack_map.items():
            group = QGroupBox(pack_name)
            group.setStyleSheet(
                "QGroupBox { color: #7CBD4D; font-weight: bold; "
                "border: 2px solid #3D3D3D; margin-top: 12px; }")
            g_layout = QVBoxLayout(group)

            btn_group = QButtonGroup(group)
            first = True
            for i, (sp_name, sp_path) in enumerate(subpacks):
                rb = QRadioButton(sp_name)
                if first:
                    rb.setChecked(True)
                    first = False
                rb.setStyleSheet("color: #C6C6C6;")
                btn_group.addButton(rb, i)
                g_layout.addWidget(rb)

            self._groups[pack_name] = (btn_group, subpacks)
            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("Confirm Selection")
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self._confirm)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _confirm(self):
        for pack_name, (btn_group, subpacks) in self._groups.items():
            idx = btn_group.checkedId()
            if idx >= 0 and idx < len(subpacks):
                self.selections[pack_name] = subpacks[idx]
        self.accept()


class VersionCheckDialog(QDialog):
    """
    Dialog showing pack versions grouped by script API version.
    Appears when user clicks "Check Packs" on the merger tab.
    """

    def __init__(self, version_groups, parent=None):
        super().__init__(parent)
        self.version_groups = version_groups
        self.setWindowTitle("Pack Version Check")
        self.setMinimumSize(650, 450)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("<b>Packs grouped by Script API version</b><br>"
                        "Packs with the same @minecraft/server version will be merged together.")
        header.setWordWrap(True)
        header.setStyleSheet("color: #C6C6C6; font-size: 11pt;")
        layout.addWidget(header)

        tree = QTreeWidget()
        tree.setHeaderLabels(["Script API Version", "Pack Name", "Format Version"])
        tree.setAlternatingRowColors(False)
        tree.setStyleSheet(
            "QTreeWidget { background-color: #252525; color: #C6C6C6; "
            "border: 2px solid #3D3D3D; } "
            "QTreeWidget::item:selected { background-color: #7CBD4D; color: #FFFFFF; } "
            "QTreeWidget::item { padding: 4px; }")

        for version, packs in sorted(self.version_groups.items()):
            version_item = QTreeWidgetItem([version, f"{len(packs)} pack(s)", ""])
            version_item.setExpanded(True)
            font = version_item.font(0)
            font.setBold(True)
            version_item.setFont(0, font)
            version_item.setForeground(0, Qt.GlobalColor.cyan)

            for pack_info in packs:
                item = QTreeWidgetItem([
                    "",
                    pack_info.get('name', 'Unknown'),
                    str(pack_info.get('format_version', ''))
                ])
                version_item.addChild(item)

            tree.addTopLevelItem(version_item)

        layout.addWidget(tree)

        # Summary
        total_packs = sum(len(packs) for packs in self.version_groups.values())
        summary = QLabel(f"<b>Total: {total_packs} pack(s) in {len(self.version_groups)} version group(s)</b>")
        summary.setStyleSheet("color: #C6C6C6;")
        layout.addWidget(summary)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("Close")
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)


class PackCustomizationDialog(QDialog):
    """
    Dialog for customizing the merged pack's name, description, icon, and author.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Merged Pack")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._custom_icon_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Pack name
        name_label = QLabel("Pack Name:")
        name_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        layout.addWidget(name_label)
        self._name_edit = QLineEdit("Merged Pack")
        self._name_edit.setStyleSheet("padding: 8px;")
        layout.addWidget(self._name_edit)

        # Pack description
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        layout.addWidget(desc_label)
        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        self._desc_edit.setPlainText("Merged behavior and resource pack")
        self._desc_edit.setStyleSheet("padding: 4px;")
        layout.addWidget(self._desc_edit)

        # Author
        author_label = QLabel("Author:")
        author_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        layout.addWidget(author_label)
        self._author_edit = QLineEdit("Anvil-MC")
        layout.addWidget(self._author_edit)

        # Pack icon
        icon_label = QLabel("Pack Icon (optional):")
        icon_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        layout.addWidget(icon_label)
        icon_btn_layout = QHBoxLayout()
        self._icon_path_label = QLabel("No icon selected (will use first pack's icon)")
        self._icon_path_label.setStyleSheet("color: #888888;")
        icon_btn_layout.addWidget(self._icon_path_label, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_icon)
        icon_btn_layout.addWidget(browse_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_icon)
        icon_btn_layout.addWidget(clear_btn)
        layout.addLayout(icon_btn_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("Apply")
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("Skip")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Pack Icon", "",
            "Images (*.png *.jpg *.jpeg)")
        if path:
            self._custom_icon_path = path
            self._icon_path_label.setText(_os.path.basename(path))

    def _clear_icon(self):
        self._custom_icon_path = None
        self._icon_path_label.setText("No icon selected (will use first pack's icon)")

    def get_customization(self):
        """Return dict with name, description, author, and optional icon path."""
        return {
            'name': self._name_edit.text().strip() or "Merged Pack",
            'description': self._desc_edit.toPlainText().strip(),
            'author': self._author_edit.text().strip() or "Anvil-MC",
            'icon_path': self._custom_icon_path,
        }


class AboutDialog(QDialog):
    """About dialog showing application info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Anvil-MC")
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

        subtitle = QLabel("Minecraft Bedrock Edition Addon Merger")
        subtitle.setStyleSheet("color: #C6C6C6; font-size: 11pt;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        version = QLabel("Version 7.0.2")
        version.setStyleSheet("color: #888888; font-size: 10pt;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(16)

        desc = QLabel(
            "A fully local tool for merging Minecraft Bedrock Edition\n"
            "addon packs with intelligent conflict resolution,\n"
            "subpack selection, and automated compatibility fixes.")
        desc.setStyleSheet("color: #B0B0B0; font-size: 10pt;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(16)

        footer = QLabel("Built with PySide6  |  ExtendedBE Fixer Framework")
        footer.setStyleSheet("color: #606060; font-size: 9pt;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()

        ok_btn = QPushButton("Close")
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(120)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
