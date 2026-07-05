"""
Custom widgets for Anvil-MC.
Includes themed status indicators and reusable UI components.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AchievementIndicator(QWidget):
    """
    Custom widget showing green checkmark or red X for achievement compatibility
    status during pack merges.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self._label = QLabel("Achievements:")
        self._label.setStyleSheet("color: #C6C6C6; font-weight: 600;")
        self._layout.addWidget(self._label)

        self._status_icon = QLabel("⏳")
        self._status_icon.setStyleSheet("color: #FFFF55; font-size: 16px;")
        self._layout.addWidget(self._status_icon)

        self._status_text = QLabel("Unknown")
        self._status_text.setStyleSheet("color: #FFFF55;")
        self._layout.addWidget(self._status_text)

        self._layout.addStretch()

        self.set_status_unknown()

    def set_status_unknown(self):
        """Set status to unknown/loading."""
        self._status_icon.setText("⏳")
        self._status_icon.setStyleSheet("color: #FFFF55; font-size: 16px;")
        self._status_text.setText("Checking...")
        self._status_text.setStyleSheet("color: #FFFF55;")

    def set_status_compatible(self):
        """Set status to achievement-compatible."""
        self._status_icon.setText("✅")
        self._status_icon.setStyleSheet("color: #55FF55; font-size: 16px;")
        self._status_text.setText("Compatible")
        self._status_text.setStyleSheet("color: #55FF55;")

    def set_status_incompatible(self):
        """Set status to achievement-incompatible."""
        self._status_icon.setText("❌")
        self._status_icon.setStyleSheet("color: #FF5555; font-size: 16px;")
        self._status_text.setText("Incompatible")
        self._status_text.setStyleSheet("color: #FF5555;")

    def set_status(self, compatible: bool):
        """Set status from boolean."""
        if compatible:
            self.set_status_compatible()
        else:
            self.set_status_incompatible()


class ThemedSeparator(QFrame):
    """A horizontal line separator with the blocky theme style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("color: #3D3D3D; margin: 4px 0px;")


class StatusLabel(QLabel):
    """A styled status label with the Minecraft theme colors."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "status-mode")
        self.setStyleSheet("color: #5CE3E6; font-weight: 600;")
