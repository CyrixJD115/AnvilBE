"""
Settings tab — application configuration panel.
Controls language, organization mode, and merge-by-version.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt
from src.core.i18n import available_languages, _tr


class SettingsTab(QWidget):
    """
    Tab for configuring application settings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── General settings ──────────────────────────────────────────
        self._general_group = QGroupBox("")
        general_layout = QVBoxLayout(self._general_group)

        # Language
        lang_row = QHBoxLayout()
        self._lang_label = QLabel()
        self._lang_label.setStyleSheet("color: #C6C6C6; font-weight: bold;")
        self._lang_combo = QComboBox()
        for _code, _name in available_languages():
            self._lang_combo.addItem(_name, _code)
        lang_row.addWidget(self._lang_label)
        lang_row.addWidget(self._lang_combo, 1)
        general_layout.addLayout(lang_row)

        layout.addWidget(self._general_group)

        # ── Merge settings ────────────────────────────────────────────
        self._merge_group = QGroupBox("")
        merge_layout = QVBoxLayout(self._merge_group)

        self._chk_modpack = QCheckBox()
        self._chk_modpack.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_modpack)

        self._chk_merge_version = QCheckBox()
        self._chk_merge_version.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_merge_version)

        self._chk_customize = QCheckBox()
        self._chk_customize.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_customize)

        self._chk_show_linked = QCheckBox()
        self._chk_show_linked.setStyleSheet("color: #C6C6C6;")
        merge_layout.addWidget(self._chk_show_linked)

        layout.addWidget(self._merge_group)

        # ── Default output directory ──────────────────────────────────
        self._output_group = QGroupBox("")
        output_layout = QHBoxLayout(self._output_group)

        self._entry_output_dir = QLineEdit()
        self._entry_output_dir.setPlaceholderText("")
        self._btn_browse = QPushButton()

        output_layout.addWidget(self._entry_output_dir, 1)
        output_layout.addWidget(self._btn_browse)

        layout.addWidget(self._output_group)

        # ── Save button ───────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_save = QPushButton()
        self._btn_save.setProperty("class", "primary")
        self._btn_save.setMinimumHeight(40)
        btn_layout.addWidget(self._btn_save)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def retranslate_ui(self):
        self._general_group.setTitle(_tr("settings.group.general", "General"))
        self._lang_label.setText(_tr("settings.language", "Language:"))
        self._merge_group.setTitle(_tr("settings.group.merge_options", "Merge Options"))
        self._chk_modpack.setText(_tr("settings.modpack_organization", "Modpack organization (group by source pack)"))
        self._chk_merge_version.setText(_tr("settings.merge_by_version", "Merge by @minecraft/server version"))
        self._chk_customize.setText(_tr("settings.customize_before_merge", "Show pack customization dialog before merge"))
        self._chk_show_linked.setText(_tr("settings.show_linked", "Show linked packs after merge"))
        self._output_group.setTitle(_tr("settings.group.default_output", "Default Output Directory"))
        self._entry_output_dir.setPlaceholderText(_tr("settings.default_output_ph", "Select default output directory..."))
        self._btn_browse.setText(_tr("common.browse", "Browse..."))
        self._btn_save.setText(_tr("settings.save_settings", "Save Settings"))

    # ── Public accessors ─────────────────────────────────────────────

    @property
    def lang_combo(self):
        return self._lang_combo

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
            "modpack_organization": self._chk_modpack.isChecked(),
            "merge_by_version": self._chk_merge_version.isChecked(),
            "customize_pack_after_merge": self._chk_customize.isChecked(),
            "show_linked_packs_after_merge": self._chk_show_linked.isChecked(),
        }

    def set_settings(self, settings):
        self.set_lang(settings.get("lang", "en"))
        self.set_output_dir(settings.get("output_dir", ""))
        self._chk_modpack.setChecked(settings.get("modpack_organization", False))
        self._chk_merge_version.setChecked(settings.get("merge_by_version", False))
        self._chk_customize.setChecked(settings.get("customize_pack_after_merge", True))
        self._chk_show_linked.setChecked(settings.get("show_linked_packs_after_merge", False))
