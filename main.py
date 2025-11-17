#!/usr/bin/env python3
"""
EEPROM Layout Editor - Main Entry Point

A cross-platform desktop application for viewing and editing EEPROM binary files
based on C header file struct definitions.
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("EEPROM Layout Editor")
    app.setOrganizationName("EepromTool")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
