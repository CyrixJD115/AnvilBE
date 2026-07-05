#!/usr/bin/env python3
"""
Anvil-MC — Minecraft Bedrock Edition Addon Merger
Entry point for the application.

Usage:
    python main.py
"""
import sys
import os
from pathlib import Path

# Add the project root to sys.path so 'src' is importable
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))


def main():
    """Launch the Anvil-MC application."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from src.app import AutoBEWindow

        app = QApplication(sys.argv)

        # Application metadata
        app.setApplicationName("Anvil-MC")
        app.setApplicationVersion("7.0.2")
        app.setOrganizationName("Anvil-MC")

        # Set window icon
        icon_path = _project_root / "src" / "theme" / "anvil.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        # Create and show main window
        window = AutoBEWindow()
        window.show()

        # Run application
        sys.exit(app.exec())

    except ImportError as e:
        print(f"Error: Missing dependency — {e}", file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error launching application: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
