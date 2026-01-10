#!/usr/bin/env python3
"""Manager Factory for MainWindow dependencies.

This module consolidates manager creation logic, extracting
factory methods from MainWindow to improve cohesion.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from philocr.ui.configuration_manager import ConfigurationManager
from philocr.ui.file_operations_manager import FileOperationsManager
from philocr.ui.format_display_manager import FormatDisplayManager
from philocr.ui.worker_callbacks import WorkerCallbacks
from philocr.ui.worker_manager import WorkerManager

if TYPE_CHECKING:
    from PyQt6.QtWidgets import (
        QProgressBar,
        QTextEdit,
        QWidget,
    )

    from philocr.utils.temp_cleaner import TempFileCleaner


class MainWindowManagerFactory:
    """Factory for creating MainWindow manager dependencies.

    Consolidates manager creation logic to improve cohesion
    and maintainability in MainWindow.
    """

    @staticmethod
    def create_format_display_manager(
        text_edit: "QTextEdit",  # noqa: F821
        html_preview: "QTextEdit",  # noqa: F821
        markdown_preview: "QTextEdit",  # noqa: F821
        json_preview: "QTextEdit",  # noqa: F821
        on_save_buttons_enable: Callable[[], None],
    ) -> FormatDisplayManager:
        """Create and configure the format display manager.

        Args:
            text_edit: Text display widget
            html_preview: HTML preview widget
            markdown_preview: Markdown preview widget
            json_preview: JSON preview widget
            on_save_buttons_enable: Callback to enable save buttons

        Returns:
            Configured FormatDisplayManager instance
        """
        return FormatDisplayManager(
            text_edit=text_edit,
            html_preview=html_preview,
            markdown_preview=markdown_preview,
            json_preview=json_preview,
            on_save_buttons_enable=on_save_buttons_enable,
        )

    @staticmethod
    def create_file_operations_manager(
        parent_widget: "QWidget",
        current_result_json_getter: Callable[[], Optional[Dict[str, Any]]],
        current_result_json_setter: Callable[[Optional[Dict[str, Any]]], None],
        format_display_manager: FormatDisplayManager,
        on_status_update: Callable[[str], None],
        on_save_buttons_enable: Callable[[], None],
    ) -> FileOperationsManager:
        """Create and configure the file operations manager.

        Args:
            parent_widget: Parent widget for dialogs
            current_result_json_getter: Callback to get current JSON data
            current_result_json_setter: Callback to set current JSON data
            format_display_manager: FormatDisplayManager instance
            on_status_update: Callback for status updates
            on_save_buttons_enable: Callback to enable save buttons

        Returns:
            Configured FileOperationsManager instance
        """
        return FileOperationsManager(
            parent_widget=parent_widget,
            current_result_json_getter=current_result_json_getter,
            current_result_json_setter=current_result_json_setter,
            format_display_manager=format_display_manager,
            on_status_update=on_status_update,
            on_save_buttons_enable=on_save_buttons_enable,
        )

    @staticmethod
    def create_worker_manager(
        temp_cleaner: "TempFileCleaner",  # noqa: F821
        progress_bar: "QProgressBar",  # noqa: F821
        on_text_update: Callable[[str], None],
        on_status_update: Callable[[str], None],
        on_error: Callable[[str], None],
        on_finished: Callable[[bool], None],
        on_json_ready: Callable[[Dict[str, Any]], None],
        on_button_state_change: Callable[[Dict[str, bool]], None],
        on_preview_clear: Callable[[], None],
    ) -> WorkerManager:
        """Create and configure the worker manager.

        Args:
            temp_cleaner: Temporary file cleaner instance
            progress_bar: Progress bar widget
            on_text_update: Callback for text updates
            on_status_update: Callback for status updates
            on_error: Callback for error messages
            on_finished: Callback for processing completion
            on_json_ready: Callback for JSON data ready
            on_button_state_change: Callback for button state changes
            on_preview_clear: Callback to clear previews

        Returns:
            Configured WorkerManager instance
        """
        worker_callbacks = WorkerCallbacks(
            on_text_update=on_text_update,
            on_status_update=on_status_update,
            on_error=on_error,
            on_finished=on_finished,
            on_json_ready=on_json_ready,
            on_button_state_change=on_button_state_change,
            on_preview_clear=on_preview_clear,
        )
        return WorkerManager(
            temp_cleaner=temp_cleaner,
            progress_bar=progress_bar,
            callbacks=worker_callbacks,
        )

    @staticmethod
    def create_configuration_manager(
        parent_widget: "QWidget",
        on_config_error: Callable[[str], None],
        on_settings_requested: Callable[[], None],
    ) -> ConfigurationManager:
        """Create and configure the configuration manager.

        Args:
            parent_widget: Parent widget for dialogs
            on_config_error: Callback for configuration errors
            on_settings_requested: Callback when settings are requested

        Returns:
            Configured ConfigurationManager instance
        """
        return ConfigurationManager(
            parent_widget=parent_widget,
            on_config_error=on_config_error,
            on_settings_requested=on_settings_requested,
        )
