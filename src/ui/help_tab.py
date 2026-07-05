"""
Help tab — built-in documentation browser for Anvil-MC.
Provides sections on overview, getting started, merging, errors, and best practices.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt

from src.core.i18n import help_content_path, current_lang


def _load_help_content(lang=None) -> str:
    """Load the help HTML content for *lang*, falling back to English."""
    try:
        with open(help_content_path(lang), 'r', encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return "<h2>Help content unavailable.</h2>"


class HelpTab(QWidget):
    """
    Tab displaying built-in documentation and help content.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setHtml(_load_help_content(current_lang()))
        self._text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #B0B0B0;
                border: 2px solid #3D3D3D;
                padding: 12px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self._text_edit)

    def retranslate_ui(self):
        """Reload help content in the current language."""
        self._text_edit.setHtml(_load_help_content(current_lang()))
