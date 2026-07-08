"""
Help tab — built-in documentation hub for Anvil-MC.

Two sub-sections:
  • Documentation — the existing help HTML content.
  • Addon Fixers — a read-only inventory of the patches that run
    automatically during the merge pipeline (demoted from a top-level tab
    into here, since it serves a documentation purpose).
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit
from PySide6.QtCore import Qt

from src.core.i18n import help_content_path, current_lang, _tr
from src.ui.fixers_view import FixersView


def _load_help_content(lang=None) -> str:
    """Load the help HTML content for *lang*, falling back to English."""
    try:
        with open(help_content_path(lang), 'r', encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return "<h2>Help content unavailable.</h2>"


class HelpTab(QWidget):
    """
    Help hub: documentation browser + addon-fixers reference.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._tabs = QTabWidget()
        # Tag the inner tab bar with property "sub" for QSS targeting.
        self._tabs.tabBar().setProperty("sub", "true")

        # ── Documentation sub-tab ─────────────────────────────────────
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #B0B0B0;
                border: 2px solid #3D3D3D;
                padding: 12px;
                font-size: 10pt;
            }
        """)
        self._tabs.addTab(self._text_edit, "")

        # ── Addon Fixers sub-tab ──────────────────────────────────────
        self._fixers_view = FixersView(compact=True)
        self._tabs.addTab(self._fixers_view, "")

        layout.addWidget(self._tabs)

    def retranslate_ui(self):
        """Reload help content + fixer list in the current language."""
        self._text_edit.setHtml(_load_help_content(current_lang()))
        self._tabs.setTabText(0, _tr("help.tab.documentation", "Documentation"))
        self._tabs.setTabText(1, _tr("help.tab.fixers", "Addon Fixers"))
        self._fixers_view.retranslate_ui()
