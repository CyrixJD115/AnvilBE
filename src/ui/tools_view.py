"""
ToolsView — unified hub for secondary utility tools.
Groups :class:`~src.ui.mcpacker_tab.MCPackerTab` and
:class:`~src.ui.list_maker_tab.ListMakerTab` behind an internal sub-tab bar
so the primary workspace stays focused.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.ui.mcpacker_tab import MCPackerTab
from src.ui.list_maker_tab import ListMakerTab
from src.core.i18n import _tr


class ToolsView(QWidget):
    """
    Container view exposing the MCPacker and List Maker tools as sub-tabs.
    Forwards the underlying tab objects via :pyattr:`mcpacker_tab` and
    :pyattr:`list_maker_tab` so app.py can keep its existing signal wiring.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mcpacker_tab = MCPackerTab()
        self.list_maker_tab = ListMakerTab()
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Heading ───────────────────────────────────────────────────
        from PySide6.QtWidgets import QLabel
        self._heading = QLabel()
        self._heading.setStyleSheet("color: #7CBD4D; font-size: 16pt; font-weight: 800;")
        layout.addWidget(self._heading)

        self._subheading = QLabel()
        self._subheading.setStyleSheet("color: #888888; font-size: 10pt;")
        self._subheading.setWordWrap(True)
        layout.addWidget(self._subheading)

        # ── Sub-tab bar ───────────────────────────────────────────────
        self._tabs = QTabWidget()
        # Tag the inner tab bar with property "sub" for QSS targeting.
        self._tabs.tabBar().setProperty("sub", "true")
        self._tabs.addTab(self.mcpacker_tab, "")
        self._tabs.addTab(self.list_maker_tab, "")
        layout.addWidget(self._tabs, 1)

    # ── i18n ──────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._heading.setText(_tr("tools.heading", "Toolkit Hub"))
        self._subheading.setText(_tr("tools.subheading",
            "Secondary utilities for packing and organizing Minecraft Bedrock content."))
        self._tabs.setTabText(0, _tr("tools.tab.packer", "Pack Utility"))
        self._tabs.setTabText(1, _tr("tools.tab.organizer", "Pack Organizer"))
        # Children self-retranslate via app._retranslate_ui() child loop,
        # but re-apply here too for safety.
        for child in (self.mcpacker_tab, self.list_maker_tab):
            if hasattr(child, "retranslate_ui"):
                child.retranslate_ui()
