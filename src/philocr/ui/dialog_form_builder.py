"""Form builder utilities for dialog forms.

This module provides reusable form field creation utilities
to reduce duplication in dialog classes.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)


class DialogFormBuilder:
    """Builder for creating form fields in dialogs."""

    @staticmethod
    def create_input_field(
        current_value: str = "",
        placeholder: str = "",
        min_width: int = 400,
    ) -> QLineEdit:
        """Create a standardized input field.

        Args:
            current_value: Current value for the field
            placeholder: Placeholder text
            min_width: Minimum width in pixels

        Returns:
            Configured QLineEdit widget
        """
        field = QLineEdit(current_value)
        field.setMinimumWidth(min_width)
        field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if placeholder:
            field.setPlaceholderText(placeholder)
        return field

    @staticmethod
    def add_file_browser_row(
        layout: QFormLayout,
        label: str,
        field: QLineEdit,
        browse_callback: Callable[[], None],
    ) -> None:
        """Add a file browser row with browse button.

        Args:
            layout: Form layout to add to
            label: Label text for the row
            field: Input field widget
            browse_callback: Callback function for browse button
        """
        creds_layout = QHBoxLayout()
        creds_layout.addWidget(field)
        browse_button = QPushButton("Browse...")
        _ = browse_button.clicked.connect(browse_callback)
        creds_layout.addWidget(browse_button)
        layout.addRow(label, creds_layout)

    @staticmethod
    def add_info_label(
        layout: QFormLayout,
        text: str,
    ) -> None:
        """Add an informational label to the form.

        Args:
            layout: Form layout to add to
            text: Information text to display
        """
        info_label = QLabel(text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addRow("", info_label)
