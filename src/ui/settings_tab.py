"""
Settings tab — application configuration panel.
Controls language, fixer options, organization mode, and merge-by-version.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt


class SettingsTab(QWidget):
    """
    Tab for configuring application settings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── General settings ──────────────────────────────────────────
        general_group = QGroupBox("General")
        general_layout = QVBoxLayout(general_group)

        # Language
        lang_row = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("English", "en")
        self._lang_combo.setToolTip("Restart required for language change")
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self._lang_combo, 1)
        general_layout.addLayout(lang_row)

        layout.addWidget(general_group)

        # ── Merge settings ────────────────────────────────────────────
        merge_group = QGroupBox("Merge Options")
        merge_layout = QVBoxLayout(merge_group)

        self._chk_fixers = QCheckBox("Enable ExtendedBE fixers")
        self._chk_fixers.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_fixers)

        self._chk_modpack = QCheckBox("Modpack organization (group by source pack)")
        self._chk_modpack.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_modpack)

        self._chk_merge_version = QCheckBox("Merge by @minecraft/server version")
        self._chk_merge_version.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_merge_version)

        self._chk_customize = QCheckBox("Show pack customization dialog after merge")
        self._chk_customize.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_customize)

        self._chk_show_linked = QCheckBox("Show linked packs after merge")
        self._chk_show_linked.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_show_linked)

        layout.addWidget(merge_group)

        # ── Default output directory ──────────────────────────────────
        output_group = QGroupBox("Default Output Directory")
        output_layout = QHBoxLayout(output_group)

        self._entry_output_dir = QLineEdit()
        self._entry_output_dir.setPlaceholderText("Select default output directory...")
        self._btn_browse = QPushButton("Browse...")

        output_layout.addWidget(self._entry_output_dir, 1)
        output_layout.addWidget(self._btn_browse)

        layout.addWidget(output_group)

        # ── Save button ───────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_save = QPushButton("Save Settings")
        self._btn_save.setProperty("class", "primary")
        self._btn_save.setMinimumHeight(40)
        btn_layout.addWidget(self._btn_save)
        layout.addLayout(btn_layout)

        layout.addStretch()

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def lang_combo(self):
        return self._lang_combo

    @property
    def chk_fixers(self):
        return self._chk_fixers

    @property
    def chk_modpack(self):
        return self._chk_modpack

    @property
    def chk_merge_version(self):
        return self._chk_merge_version

    @property
    def chk_customize(self):
        return self._chk_customize

    @property
    def chk_show_linked(self):
        return self._chk_show_linked

    @property
    def entry_output_dir(self):
        return self._entry_output_dir

    @property
    def btn_browse(self):
        return self._btn_browse

    @property
    def btn_save(self):
        return self._btn_save

    def get_output_dir(self):
        return self._entry_output_dir.text().strip()

    def set_output_dir(self, path):
        self._entry_output_dir.setText(path)

    def get_lang(self):
        return self._lang_combo.currentData()

    def set_lang(self, code):
        idx = self._lang_combo.findData(code)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

    def get_settings(self):
        return {
            "lang": self.get_lang(),
            "output_dir": self.get_output_dir(),
            "fixers_enabled": self._chk_fixers.isChecked(),
            "modpack_organization": self._chk_modpack.isChecked(),
            "merge_by_version": self._chk_merge_version.isChecked(),
            "customize_pack_after_merge": self._chk_customize.isChecked(),
            "show_linked_packs_after_merge": self._chk_show_linked.isChecked(),
        }

    def set_settings(self, settings):
        self.set_lang(settings.get("lang", "en"))
        self.set_output_dir(settings.get("output_dir", ""))
        self._chk_fixers.setChecked(settings.get("fixers_enabled", False))
        self._chk_modpack.setChecked(settings.get("modpack_organization", False))
        self._chk_merge_version.setChecked(settings.get("merge_by_version", False))
        self._chk_customize.setChecked(settings.get("customize_pack_after_merge", False))
        self._chk_show_linked.setChecked(settings.get("show_linked_packs_after_merge", False))
