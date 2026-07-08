"""
Sidebar navigation for the Anvil-MC shell.
A vertical rail of checkable tool-buttons for switching views, with the
console toggle pinned to the bottom along with the Settings / Help entries.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QPushButton, QLabel, QButtonGroup,
    QSizePolicy, QStyle, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from src.core.i18n import _tr


class SidebarNav(QWidget):
    """
    Left navigation rail.

    Emits:
      - view_requested(str)  when a nav button is clicked.
        Payload is one of: 'dashboard', 'tools', 'recents',
        'console', 'settings', 'help'.
    """

    view_requested = Signal(str)


    # (id, i18n key, fallback, QStyle.StandardPixmap)
    _PRIMARY = (
        ("dashboard", "nav.dashboard", "Dashboard", QStyle.SP_FileDialogContentsView),
        ("tools", "nav.tools", "Tools", QStyle.SP_FileDialogDetailedView),
        ("recents", "nav.recents", "Recents", QStyle.SP_BrowserReload),
    )
    _PINNED = (
        ("console", "nav.console", "Console", QStyle.SP_CommandLink),
        ("settings", "nav.settings", "Settings", QStyle.SP_ComputerIcon),
        ("help", "nav.help", "Help", QStyle.SP_MessageBoxInformation),
    )

    def __init__(self, app_version: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self._app_version = app_version
        self._nav_buttons = {}   # id -> QPushButton
        em = self.fontMetrics().size(0, "x").height()
        self._icon_size = QSize(em, em)
        self._setup_ui()
        self._retranslate()

    # ── Icons ────────────────────────────────────────────────────────
    @staticmethod
    def _std_icon(pixmap: QStyle.StandardPixmap) -> QIcon:
        """Return a built-in Qt standard icon for the given standard pixmap."""
        app = QApplication.instance()
        if app is None:
            return QIcon()
        return app.style().standardIcon(pixmap)

    # ── Setup ─────────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Brand ─────────────────────────────────────────────────────
        self._brand = QLabel("ANVIL-MC")
        self._brand.setProperty("class", "nav-brand")
        root.addWidget(self._brand)

        self._version_label = QLabel(self._app_version)
        self._version_label.setProperty("class", "nav-version")
        root.addWidget(self._version_label)

        root.addWidget(self._make_divider())

        # ── Primary nav (Workspace) ───────────────────────────────────
        self._workspace_header = QLabel()
        self._workspace_header.setProperty("class", "nav-section")
        root.addWidget(self._workspace_header)

        self._primary_group = QButtonGroup(self)
        self._primary_group.setExclusive(True)
        for nav_id, key, fallback, glyph in self._PRIMARY:
            btn = self._make_nav_button(nav_id, glyph)
            self._primary_group.addButton(btn)
            root.addWidget(btn)
            self._nav_buttons[nav_id] = btn

        # Flexible spacer pushes the SYSTEM (Settings/Help) and MONITOR
        # (Console) sections to the bottom of the sidebar, isolating them
        # from the primary workspace nav as required.
        root.addStretch(1)

        root.addWidget(self._make_divider())

        # ── Pinned SYSTEM section (Settings + Help) ───────────────────
        self._system_header = QLabel()
        self._system_header.setProperty("class", "nav-section")
        root.addWidget(self._system_header)

        # Settings + Help + Console
        self._pinned_group = QButtonGroup(self)
        self._pinned_group.setExclusive(True)
        for nav_id, key, fallback, glyph in self._PINNED:
            btn = self._make_nav_button(nav_id, glyph)
            self._pinned_group.addButton(btn)
            root.addWidget(btn)
            self._nav_buttons[nav_id] = btn

    def _make_nav_button(self, nav_id: str, std_icon) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(self._std_icon(std_icon))
        btn.setIconSize(self._icon_size)
        btn.setProperty("nav", "true")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.clicked.connect(lambda _checked=False, vid=nav_id: self.view_requested.emit(vid))
        return btn

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setProperty("class", "nav-divider")
        line.setFrameShape(QFrame.NoFrame)
        return line

    # ── Public API ────────────────────────────────────────────────────
    def select(self, view_id: str):
        """Programmatically check the nav button for *view_id*."""
        btn = self._nav_buttons.get(view_id)
        if btn is not None:
            btn.setChecked(True)

    # ── i18n ──────────────────────────────────────────────────────────
    def retranslate_ui(self):
        self._retranslate()

    def _retranslate(self):
        self._workspace_header.setText(_tr("nav.section.workspace", "WORKSPACE"))
        self._system_header.setText(_tr("nav.section.system", "SYSTEM"))
        for nav_id, key, fallback, std_icon in self._PRIMARY + self._PINNED:
            btn = self._nav_buttons.get(nav_id)
            if btn is not None:
                # Icon already set in _make_nav_button; just refresh text.
                btn.setText(_tr(key, fallback))
