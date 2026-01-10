#!/usr/bin/env python3
"""
A simple test script to check if icons can be loaded properly.
Run this script from the project root directory.
"""

import logging
import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from philocr.ui.icon_loader import load_application_icon

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("icon_test")


def list_icon_files(directory: str) -> list[str]:
    """Lists all potential icon files in a directory."""
    if not os.path.exists(directory):
        logger.error(f"Directory does not exist: {directory}")
        return []

    logger.info(f"Checking directory: {directory}")
    files = os.listdir(directory)
    icon_files = [f for f in files if f.endswith((".png", ".icns", ".ico"))]

    for icon in icon_files:
        logger.info(f"Found icon file: {icon}")

    return icon_files


class TestWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Set up the window
        self.setWindowTitle("Icon Loading Test")
        self.setMinimumSize(500, 300)

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Create a label to display information
        self.info_label = QLabel("Testing icon loading...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        # Create a label to display the icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.setCentralWidget(central_widget)

        # Test icon loading
        success: bool
        icon_path: str
        success, icon_path = load_application_icon(self)

        if success:
            self.info_label.setText(f"Successfully loaded icon:\n{icon_path}")

            # Also display the icon in the window
            try:
                pixmap = QPixmap(icon_path)
                self.icon_label.setPixmap(
                    pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
                )
            except Exception as e:
                logger.error(f"Error displaying icon: {e}")
        else:
            self.info_label.setText("Failed to load any icons!")

        # List all available icon files
        base_path = os.path.dirname(os.path.realpath(__file__))
        icon_folder = os.path.join(base_path, "philocr_icons")
        list_icon_files(icon_folder)
        # Optionally, log or display icon_files if needed


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
