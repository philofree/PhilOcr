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
    QWidget,
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
            text_edit.setFont(QFont("Gentium", font_size))

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
        header_frame.setStyleSheet("background-color: #f0f0f0;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 2, 5, 15)
        header_layout.setSpacing(10)

        # Title and version row - centered
        title_row = QHBoxLayout()
        title_row.addStretch()
        
        app_title = QLabel(f"{app_name}")
        title_font = QFont("Gentium", 34, QFont.Weight.Bold)
        title_font.setItalic(True)
        app_title.setFont(title_font)
        app_title.setStyleSheet("color: #1e3a6e;")
        title_row.addWidget(app_title)

        version_label = QLabel("v3.0")
        version_label.setFont(QFont("Gentium", 22))
        title_font.setItalic(True)
        version_label.setStyleSheet("color: #1e3a6e;")
        title_row.addWidget(version_label)
        
        title_row.addStretch()
        header_layout.addLayout(title_row)

        # Buttons - side-by-side with centering
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(5)

        button_font = QFont("Gentium", 14)
        
        settings_button = WidgetFactory.create_button(
            "Settings",
            on_settings_clicked,
            tooltip="Configure Google Cloud credentials",
            min_height=36,
            max_width=200,
        )
        settings_button.setFont(button_font)
        button_container_layout.addWidget(settings_button)

        about_button = WidgetFactory.create_button(
            "About",
            on_about_clicked,
            tooltip="Show information about this application",
            min_height=36,
            max_width=200,
        )
        about_button.setFont(button_font)
        button_container_layout.addWidget(about_button)

        # Center the buttons horizontally
        centering_wrapper = QWidget()
        centering_layout = QHBoxLayout(centering_wrapper)
        centering_layout.setContentsMargins(0, 0, 0, 0)
        centering_layout.addStretch()
        centering_layout.addWidget(button_container)
        centering_layout.addStretch()
        header_layout.addWidget(centering_wrapper)

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
        status_label.setFont(QFont("Gentium", 14, QFont.Weight.Bold))

        status_text = QLabel("PhilOcr v3.0")
        status_text.setFont(QFont("Gentium", 14))
        status_text.setStyleSheet("color: #1e3a6e;")

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
