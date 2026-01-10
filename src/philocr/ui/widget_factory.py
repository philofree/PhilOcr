"""Widget factory for creating common UI widgets.

This module provides factory methods for creating and configuring
common PyQt6 widgets with consistent styling.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class WidgetFactory:
    """Factory for creating and configuring UI widgets."""

    @staticmethod
    def create_text_edit(
        font_families: list[str] | None = None,
        font_size: int = 12,
        read_only: bool = True,
    ) -> QTextEdit:
        """Create a configured text edit widget.

        Args:
            font_families: List of font families to use, None for default
            font_size: Font size in points
            read_only: Whether the text edit should be read-only

        Returns:
            Configured QTextEdit widget
        """
        text_edit = QTextEdit()
        text_edit.setReadOnly(read_only)

        if font_families:
            font = QFont()
            font.setFamilies(font_families)
            font.setPointSize(font_size)
            text_edit.setFont(font)
        else:
            text_edit.setFont(QFont("Courier New", font_size))

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        text_edit.setPalette(palette)
        text_edit.setStyleSheet("background-color: white; color: black;")

        return text_edit

    @staticmethod
    def create_text_area_frame() -> tuple[QFrame, QTextEdit]:
        """Create a text display area with frame.

        Returns:
            Tuple of (text frame, text edit widget)
        """
        text_frame = QFrame()
        text_frame.setStyleSheet("background-color: white; border-radius: 4px;")
        text_frame_layout = QVBoxLayout(text_frame)
        text_frame_layout.setContentsMargins(2, 2, 2, 2)

        text_edit = WidgetFactory.create_text_edit(font_size=14)
        text_frame_layout.addWidget(text_edit)

        return text_frame, text_edit

    @staticmethod
    def create_button(
        text: str,
        callback: Callable[[], None],
        enabled: bool = True,
        tooltip: str | None = None,
        max_width: int | None = None,
        min_height: int = 48,
    ) -> QPushButton:
        """Create a configured button widget.

        Args:
            text: Button text
            callback: Click callback function
            enabled: Whether button is initially enabled
            tooltip: Optional tooltip text
            max_width: Optional maximum width
            min_height: Minimum height in pixels

        Returns:
            Configured QPushButton widget
        """
        button = QPushButton(text)
        button.setMinimumHeight(min_height)
        _ = button.clicked.connect(callback)
        button.setEnabled(enabled)
        if tooltip:
            button.setToolTip(tooltip)
        if max_width:
            button.setMaximumWidth(max_width)
        return button

    @staticmethod
    def create_header_frame(
        app_name: str,
        app_version: str,
        on_settings_clicked: Callable[[], None],
        on_about_clicked: Callable[[], None],
    ) -> QFrame:
        """Create the application header frame.

        Args:
            app_name: Application name
            app_version: Application version
            on_settings_clicked: Settings button callback
            on_about_clicked: About button callback

        Returns:
            Configured header frame
        """
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("background-color: #f0f0f0;")
        header_layout = QHBoxLayout(header_frame)

        app_title = QLabel(f"{app_name}")
        app_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(app_title)

        version_label = QLabel(f"v{app_version}")
        version_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(version_label)

        header_layout.addStretch()

        settings_button = WidgetFactory.create_button(
            "Settings",
            on_settings_clicked,
            tooltip="Configure Google Cloud credentials",
        )
        header_layout.addWidget(settings_button)

        about_button = WidgetFactory.create_button(
            "About", on_about_clicked, tooltip="Show information about this application"
        )
        header_layout.addWidget(about_button)

        return header_frame

    @staticmethod
    def create_status_frame() -> tuple[QFrame, QLabel]:
        """Create the status section frame.

        Returns:
            Tuple of (status frame, status label widget)
        """
        status_frame = QFrame()
        status_frame.setMaximumHeight(60)
        status_layout = QHBoxLayout(status_frame)

        status_label = QLabel("Status:")
        status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        status_text = QLabel("Ready to process documents")
        status_text.setFont(QFont("Arial", 14))

        status_layout.addWidget(status_label)
        status_layout.addWidget(status_text, 1)

        return status_frame, status_text

    @staticmethod
    def create_progress_bar() -> QProgressBar:
        """Create a progress bar widget.

        Returns:
            Configured QProgressBar widget
        """
        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setMinimumHeight(30)
        return progress_bar
