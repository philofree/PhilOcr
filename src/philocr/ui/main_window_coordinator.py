"""Main window event coordination and orchestration.

This module provides coordination logic for MainWindow events,
reducing the complexity of the main window class by handling
cross-component interactions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog
    from PyQt6.QtWidgets import QLabel, QProgressBar, QPushButton, QTextEdit

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class MainWindowCoordinator:
    """Coordinates events and interactions in the main window.

    Handles cross-component communication and reduces coupling
    between MainWindow and its managers.
    """

    def __init__(
        self,
        status_label: QLabel,
        status_bar: Any,  # QStatusBar
        progress_bar: QProgressBar,
        buttons: dict[str, QPushButton],
    ) -> None:
        """Initialize the coordinator.

        Args:
            status_label: Status text label widget
            status_bar: Status bar widget
            progress_bar: Progress bar widget
            buttons: Dictionary of button references
        """
        self.status_label = status_label
        self.status_bar = status_bar
        self.progress_bar = progress_bar
        self.buttons = buttons

    def update_status(self, message: str) -> None:
        """Update the status message.

        Args:
            message: Status message to display
        """
        self.status_label.setText(message)
        self.status_bar.showMessage(message, 5000)

    def update_text_content(self, text_edit: QTextEdit, text: str) -> None:
        """Update text content in a text edit widget.

        Args:
            text_edit: Text edit widget to update
            text: Text content to set
        """
        text_edit.setPlainText(text)

    def set_button_states(self, states: dict[str, bool]) -> None:
        """Update button enabled/disabled states.

        Args:
            states: Dictionary mapping button names to enabled state
        """
        for button_name, enabled in states.items():
            if button_name in self.buttons:
                self.buttons[button_name].setEnabled(enabled)
            else:
                logger.warning(
                    "unknown_button_name",
                    button_name=button_name,
                    available_buttons=list(self.buttons.keys()),
                )

    def enable_save_buttons(
        self,
        has_text: bool,
        has_json: bool,
    ) -> None:
        """Enable save buttons based on content availability.

        Args:
            has_text: Whether text content is available
            has_json: Whether JSON content is available
        """
        self.set_button_states(
            {
                "save": has_text,
                "save_json": has_json,
                "save_html": has_json,
                "save_markdown": has_json,
            }
        )

    def clear_previews(
        self,
        text_edit: QTextEdit,
        markdown_preview: QTextEdit,
        html_preview: QTextEdit,
        json_preview: QTextEdit,
    ) -> None:
        """Clear all preview content.

        Args:
            text_edit: Main text edit widget
            markdown_preview: Markdown preview widget
            html_preview: HTML preview widget
            json_preview: JSON preview widget
        """
        text_edit.clear()
        markdown_preview.clear()
        html_preview.clear()
        json_preview.clear()

    def reset_processing_state(self) -> None:
        """Reset UI state after processing completion."""
        self.set_button_states(
            {
                "select": True,
                "batch": True,
                "clear": True,
            }
        )
