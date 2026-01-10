#!/usr/bin/env python3
"""State Manager for MainWindow UI state.

This module handles UI state transitions including button states,
preview clearing, and state resets.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QLabel, QProgressBar, QPushButton, QTextEdit


class MainWindowStateManager:
    """Manages UI state transitions for MainWindow.

    Handles button state management, preview clearing, and
    state reset operations to improve cohesion in MainWindow.
    """

    def __init__(
        self,
        buttons: dict[str, QPushButton],
        text_edit: QTextEdit,
        html_preview: QTextEdit,
        json_preview: QTextEdit,
        markdown_preview: QTextEdit,
        progress_bar: QProgressBar,
        status_label: QLabel,
        coordinator: Any,  # MainWindowCoordinator
    ) -> None:
        """Initialize the State Manager.

        Args:
            buttons: Dictionary of button widgets
            text_edit: Text display widget
            html_preview: HTML preview widget
            json_preview: JSON preview widget
            markdown_preview: Markdown preview widget
            progress_bar: Progress bar widget
            status_label: Status label widget
            coordinator: MainWindowCoordinator instance
        """
        self.buttons = buttons
        self.text_edit = text_edit
        self.html_preview = html_preview
        self.json_preview = json_preview
        self.markdown_preview = markdown_preview
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.coordinator = coordinator

    def set_button_states(self, states: dict[str, bool]) -> None:
        """Set button enabled states.

        Args:
            states: Dictionary mapping button names to enabled states
        """
        for button_name, enabled in states.items():
            if button_name in self.buttons:
                self.buttons[button_name].setEnabled(enabled)

    def enable_save_buttons(self) -> None:
        """Enable all save buttons."""
        self.coordinator.set_button_states(
            {
                "save": True,
                "save_json": True,
                "save_html": True,
                "save_markdown": True,
            }
        )

    def clear_previews(self) -> None:
        """Clear all preview displays with processing message."""
        self.text_edit.setPlainText("Processing...")
        self.html_preview.setHtml("<html><body><p>Processing...</p></body></html>")
        self.json_preview.setPlainText("")

    def reset_to_initial_state(self) -> None:
        """Reset UI to initial state after clearing results."""
        self.coordinator.update_status("Ready to process documents")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        # Disable save buttons
        self.set_button_states(
            {
                "save": False,
                "save_json": False,
                "save_html": False,
                "save_markdown": False,
            }
        )
