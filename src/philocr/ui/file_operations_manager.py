#!/usr/bin/env python3
"""File Operations Manager for MainWindow.

This module handles file selection, loading, and saving operations.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from philocr.utils.document_ai_formatter import extract_text_only
from philocr.utils.exceptions import FileLoadError
from philocr.utils.exceptions import FileNotFoundError as PhilOcrFileNotFoundError
from philocr.utils.exceptions import FileSaveError
from philocr.utils.file_io import (
    HTMLSaver,
    JSONLoader,
    JSONSaver,
    MarkdownSaver,
    TextSaver,
)

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class FileOperationsManager:
    """Manages file selection, loading, and saving operations."""

    def __init__(
        self,
        parent_widget: QWidget,
        current_result_json_getter: Callable[[], dict[str, Any] | None],
        current_result_json_setter: Callable[[dict[str, Any] | None], None],
        format_display_manager: Any,  # FormatDisplayManager
        on_status_update: Callable[[str], None],
        on_save_buttons_enable: Callable[[], None],
    ) -> None:
        """Initialize the File Operations Manager.

        Args:
            parent_widget: Parent widget for dialogs
            current_result_json_getter: Callback to get current JSON data
            current_result_json_setter: Callback to set current JSON data
            format_display_manager: FormatDisplayManager instance
            on_status_update: Callback for status updates
            on_save_buttons_enable: Callback to enable save buttons
        """
        self.parent_widget = parent_widget
        self.get_current_result_json = current_result_json_getter
        self.set_current_result_json = current_result_json_setter
        self.format_display_manager = format_display_manager
        self.on_status_update = on_status_update
        self.on_save_buttons_enable = on_save_buttons_enable

    def select_single_file(self) -> str | None:
        """Handle file selection for a single PDF.

        Returns:
            Selected file path or None if cancelled
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget, "Select PDF File", "", "PDF Files (*.pdf)"
        )
        return file_path if file_path else None

    def select_multiple_files(self) -> list[str] | None:
        """Handle selection of multiple PDF files for batch processing.

        Returns:
            List of selected file paths or None if cancelled
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.parent_widget, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        return file_paths if file_paths else None

    def save_text(self) -> None:
        """Save the extracted text to a file."""
        current_json = self.get_current_result_json()
        if not current_json:
            _ = QMessageBox.information(
                self.parent_widget,
                "Nothing to Save",
                "There is no extracted text to save.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save Text File",
            "extracted_text.txt",
            "Text Files (*.txt);;All Files (*.*)",
        )

        if file_path:
            try:
                text_content = extract_text_only(current_json)
                TextSaver.save_text(text_content, file_path)
                self.on_status_update(f"Text saved to {file_path}")
            except FileSaveError as e:
                logger.error(
                    "text_file_save_failed",
                    file_path=file_path,
                    error=str(e),
                    exc_info=True,
                )
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Save Error",
                    f"An error occurred while saving the file:\n{e}",
                )

    def save_json(self) -> None:
        """Save the results as JSON."""
        current_json = self.get_current_result_json()
        if not current_json:
            _ = QMessageBox.information(
                self.parent_widget,
                "Nothing to Save",
                "There is no JSON data to save.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save JSON File",
            "document_results.json",
            "JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            try:
                JSONSaver.save_json(current_json, file_path)
                self.on_status_update(f"JSON saved to {file_path}")
            except FileSaveError as e:
                logger.error(
                    "json_file_save_failed",
                    file_path=file_path,
                    error=str(e),
                    exc_info=True,
                )
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Save Error",
                    f"An error occurred while saving the JSON file:\n{e}",
                )

    def save_html(self) -> None:
        """Save the results as HTML."""
        current_json = self.get_current_result_json()
        if not current_json:
            _ = QMessageBox.information(
                self.parent_widget,
                "Nothing to Save",
                "There is no data to save as HTML.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save HTML File",
            "document_results.html",
            "HTML Files (*.html);;All Files (*.*)",
        )

        if file_path:
            try:
                HTMLSaver.save_html(current_json, file_path)
                self.on_status_update(f"HTML saved to {file_path}")
            except FileSaveError as e:
                logger.error(
                    "html_file_save_failed",
                    file_path=file_path,
                    error=str(e),
                    exc_info=True,
                )
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Save Error",
                    f"An error occurred while saving the HTML file:\n{e}",
                )

    def save_markdown(self) -> None:
        """Save the results as Markdown."""
        current_json = self.get_current_result_json()
        if not current_json:
            _ = QMessageBox.information(
                self.parent_widget,
                "Nothing to Save",
                "There is no data to save as Markdown.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save Markdown File",
            "document_results.md",
            "Markdown Files (*.md);;All Files (*.*)",
        )

        if file_path:
            try:
                full_markdown = self.format_display_manager.get_full_markdown_content()
                MarkdownSaver.save_markdown(full_markdown, file_path, current_json)
                self.on_status_update(f"Markdown saved to {file_path}")
            except (FileSaveError, ValueError) as e:
                logger.error(
                    "markdown_file_save_failed",
                    file_path=file_path,
                    error=str(e),
                    exc_info=True,
                )
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Save Error",
                    f"An error occurred while saving the Markdown file:\n{e}",
                )

    def load_json(self) -> None:
        """Load a previously saved JSON file and render it in the UI."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget,
            "Load JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            try:
                loaded_json = JSONLoader.load_json(file_path)
                self.set_current_result_json(loaded_json)

                # Update all preview tabs
                self.format_display_manager.update_all_previews(loaded_json)

                # Enable save buttons
                self.on_save_buttons_enable()

                # Update status
                file_name = os.path.basename(file_path)
                self.on_status_update(f"Loaded JSON from {file_name}")
            except (PhilOcrFileNotFoundError, FileLoadError) as e:
                logger.error(
                    "json_file_not_found",
                    file_path=file_path,
                    error=str(e),
                )
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Load Error",
                    f"File not found:\n{e}",
                )
            except Exception as e:
                logger.error(
                    "json_file_load_failed",
                    file_path=file_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                _ = QMessageBox.critical(
                    self.parent_widget,
                    "Load Error",
                    f"Error loading JSON file: {str(e)}",
                )
                raise RuntimeError(
                    f"CRITICAL: JSON file load failed - {e}"
                ) from e
