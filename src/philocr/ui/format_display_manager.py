#!/usr/bin/env python3
"""Format Display Manager for MainWindow.

This module handles format conversions and preview tab updates for JSON,
HTML, Markdown, and Text formats.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.utils.markdown_preview_helper import (
    MAX_PREVIEW_LENGTH as DEFAULT_MAX_PREVIEW_LENGTH,
)
from philocr.utils.preview_generator import generate_all_previews

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class FormatDisplayManager:
    """Manages format conversion and display updates."""

    MAX_PREVIEW_LENGTH = DEFAULT_MAX_PREVIEW_LENGTH  # Limit to 50K characters

    def __init__(
        self,
        text_edit: Any,  # QTextEdit
        html_preview: Any,  # QTextEdit
        markdown_preview: Any,  # QTextEdit
        json_preview: Any,  # QTextEdit
        on_save_buttons_enable: Callable[[], None],
    ) -> None:
        """Initialize the Format Display Manager.

        Args:
            text_edit: Text display widget
            html_preview: HTML preview widget
            markdown_preview: Markdown preview widget
            json_preview: JSON preview widget
            on_save_buttons_enable: Callback to enable save buttons
        """
        self.text_edit = text_edit
        self.html_preview = html_preview
        self.markdown_preview = markdown_preview
        self.json_preview = json_preview
        self.on_save_buttons_enable = on_save_buttons_enable
        self.full_markdown_content: str | None = None

    def update_all_previews(self, json_data: dict[str, Any]) -> None:
        """Update all preview tabs with converted content from JSON data.

        Args:
            json_data: The JSON data to convert and display
        """
        if not json_data:
            logger.error("json_data_empty")
            return

        # Use preview generator to create all preview content
        preview_content = generate_all_previews(json_data, self.MAX_PREVIEW_LENGTH)

        # Update all preview widgets
        self.json_preview.setPlainText(preview_content.json_preview)
        self.text_edit.setPlainText(preview_content.text)
        self.html_preview.setHtml(preview_content.html)

        # Store full markdown content and display preview
        self.full_markdown_content = preview_content.full_markdown
        self.markdown_preview.setPlainText(preview_content.markdown_preview)

        # Enable save buttons
        self.on_save_buttons_enable()

    def _update_markdown_preview(self, json_data: dict[str, Any]) -> None:
        """Update the markdown preview with converted content.

        Note: This method is kept for backward compatibility but is now
        handled by update_all_previews using generate_all_previews.

        Args:
            json_data: The JSON data to convert to markdown
        """
        # This method is now deprecated - use update_all_previews instead
        # Keeping for compatibility but delegating to main update method
        self.update_all_previews(json_data)

    def get_full_markdown_content(self) -> str | None:
        """Get the full markdown content for saving.

        Returns:
            The full markdown content or None if not available
        """
        return self.full_markdown_content

    def set_full_markdown_content(self, content: str | None) -> None:
        """Set the full markdown content.

        Args:
            content: The markdown content to store
        """
        self.full_markdown_content = content

    def clear_previews(self) -> None:
        """Clear all preview displays."""
        self.text_edit.setPlainText("")
        self.html_preview.setHtml("")
        self.markdown_preview.setPlainText("")
        self.json_preview.setPlainText("")
        self.full_markdown_content = None
