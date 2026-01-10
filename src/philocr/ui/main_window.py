#!/usr/bin/env python3
"""Main application window for the OJD OCR app."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStatusBar

from philocr.ui.dialog_manager import DialogManager
from philocr.ui.file_operations_manager import FileOperationsManager
from philocr.ui.format_display_manager import FormatDisplayManager
from philocr.ui.lifecycle_manager import LifecycleManager
from philocr.ui.main_window_coordinator import MainWindowCoordinator
from philocr.ui.main_window_factory import MainWindowManagerFactory
from philocr.ui.main_window_state_manager import MainWindowStateManager
from philocr.ui.ui_builder import UICallbacks
from philocr.ui.ui_composer import MainWindowUI, MainWindowUIComposer
from philocr.ui.worker_manager import WorkerManager
from philocr.utils.markdown_debug_service import MarkdownDebugService
from philocr.utils.markdown_preview_helper import MAX_PREVIEW_LENGTH
from philocr.utils.temp_cleaner import TempFileCleaner

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window for the PhilOcr app."""

    def __init__(
        self,
        app_version: str,
        app_name: str,
        app_copyright: str,
        app_description: str,
    ) -> None:
        """Initialize the MainWindow.

        Args:
            app_version: Application version string
            app_name: Application name
            app_copyright: Copyright string
            app_description: Application description
        """
        super().__init__()
        self.app_version = app_version
        self.app_name = app_name
        self.app_copyright = app_copyright
        self.app_description = app_description

        self.setWindowTitle(f"{app_name} v{app_version}")
        self.resize(1000, 800)

        # Initialize the temp file cleaner
        self.temp_cleaner = TempFileCleaner()

        # Initialize status bar
        status_bar = self.statusBar()
        assert status_bar is not None
        self.status_bar: QStatusBar = status_bar

        # Initialize state
        self.current_result_json: dict[str, Any] | None = None

        # Compose UI
        callbacks = UICallbacks(
            on_settings_clicked=self.show_settings_dialog,
            on_about_clicked=self.show_about_dialog,
            on_select_file=self.select_file,
            on_batch_files=self.select_multiple_files,
            on_load_json=self.load_json,
            on_save_text=self.save_text,
            on_save_markdown=self.save_markdown,
            on_save_json=self.save_json,
            on_save_html=self.save_html,
            on_clear=self.clear_results,
            on_debug_markdown=self.debug_markdown,
        )
        composer = MainWindowUIComposer(
            app_name=self.app_name,
            app_version=self.app_version,
            callbacks=callbacks,
        )
        self.ui = composer.compose_ui()
        composer.setup_initial_content(self.ui.text_edit)
        self.setCentralWidget(self.ui.main_widget)

        # Initialize coordinator and state manager
        buttons = {
            "select": self.ui.select_button,
            "batch": self.ui.batch_button,
            "load_json": self.ui.load_json_button,
            "save": self.ui.save_button,
            "save_markdown": self.ui.save_markdown_button,
            "save_json": self.ui.save_json_button,
            "save_html": self.ui.save_html_button,
            "clear": self.ui.clear_button,
        }
        self.coordinator = MainWindowCoordinator(
            status_label=self.ui.status_text,
            status_bar=self.status_bar,
            progress_bar=self.ui.progress_bar,
            buttons=buttons,
        )
        self.state_manager = MainWindowStateManager(
            buttons=buttons,
            text_edit=self.ui.text_edit,
            html_preview=self.ui.html_preview,
            json_preview=self.ui.json_preview,
            markdown_preview=self.ui.markdown_preview,
            progress_bar=self.ui.progress_bar,
            status_label=self.ui.status_text,
            coordinator=self.coordinator,
        )

        # Initialize managers
        factory = MainWindowManagerFactory()
        self.format_display_manager = factory.create_format_display_manager(
            text_edit=self.ui.text_edit,
            html_preview=self.ui.html_preview,
            markdown_preview=self.ui.markdown_preview,
            json_preview=self.ui.json_preview,
            on_save_buttons_enable=self.state_manager.enable_save_buttons,
        )
        self.file_operations_manager = (
            factory.create_file_operations_manager(
                parent_widget=self,
                current_result_json_getter=lambda: self.current_result_json,
                current_result_json_setter=lambda x: setattr(
                    self, "current_result_json", x
                ),
                format_display_manager=self.format_display_manager,
                on_status_update=self.update_status,
                on_save_buttons_enable=(
                    self.state_manager.enable_save_buttons
                ),
            )
        )
        self.worker_manager = factory.create_worker_manager(
            temp_cleaner=self.temp_cleaner,
            progress_bar=self.ui.progress_bar,
            on_text_update=self.update_text,
            on_status_update=self.update_status,
            on_error=self.show_error,
            on_finished=self.processing_finished,
            on_json_ready=self.json_data_ready,
            on_button_state_change=self.state_manager.set_button_states,
            on_preview_clear=self.state_manager.clear_previews,
        )
        self.config_manager = factory.create_configuration_manager(
            parent_widget=self,
            on_config_error=self.show_error,
            on_settings_requested=self.show_settings_dialog,
        )
        self.dialog_manager = DialogManager(
            parent_widget=self,
            app_name=self.app_name,
            app_version=self.app_version,
            app_copyright=self.app_copyright,
            app_description=self.app_description,
            on_config_check=self.config_manager.check,
        )
        self.lifecycle_manager = LifecycleManager(
            temp_cleaner=self.temp_cleaner,
            on_status_update=self.update_status,
        )

        # Set initial status message
        self.coordinator.update_status(f"{self.app_name} v{app_version}")

        # Check configuration after a short delay
        _ = QTimer.singleShot(500, self.config_manager.check)

    def update_status(self, message: str) -> None:
        """Update the status message.

        Args:
            message: Status message to display
        """
        self.coordinator.update_status(message)

    def update_text(self, text: str) -> None:
        """Update the text area with new text.

        Args:
            text: Text content to display
        """
        self.coordinator.update_text_content(self.ui.text_edit, text)

    def show_error(self, message: str) -> None:
        """Show an error message.

        Args:
            message: Error message to display
        """
        _ = QMessageBox.critical(self, "Error", message)

    def show_settings_dialog(self) -> None:
        """Show the settings/credentials dialog."""
        self.dialog_manager.show_settings()

    def show_about_dialog(self) -> None:
        """Show the about dialog."""
        self.dialog_manager.show_about()

    def select_file(self) -> None:
        """Handle file selection for a single PDF."""
        file_path = self.file_operations_manager.select_single_file()
        if file_path:
            self.worker_manager.start_single_file_processing(file_path)

    def select_multiple_files(self) -> None:
        """Handle selection of multiple PDF files for batch processing."""
        file_paths = self.file_operations_manager.select_multiple_files()
        if file_paths:
            self.worker_manager.start_batch_processing(file_paths)

    def json_data_ready(self, json_data: dict[str, Any]) -> None:
        """Handle JSON data ready from worker thread.

        Args:
            json_data: JSON data from processing
        """
        self.current_result_json = json_data
        self.format_display_manager.update_all_previews(json_data)

    def save_text(self) -> None:
        """Save the extracted text to a file."""
        self.file_operations_manager.save_text()

    def save_json(self) -> None:
        """Save the results as JSON."""
        self.file_operations_manager.save_json()

    def save_html(self) -> None:
        """Save the results as HTML."""
        self.file_operations_manager.save_html()

    def save_markdown(self) -> None:
        """Save the results as Markdown."""
        self.file_operations_manager.save_markdown()

    def load_json(self) -> None:
        """Load a previously saved JSON file and render it in the UI."""
        self.file_operations_manager.load_json()
        # Switch to Text tab after loading
        _ = self.ui.tab_widget.setCurrentIndex(0)

    def clear_results(self) -> None:
        """Clear all results and reset the UI."""
        self.format_display_manager.clear_previews()
        self.current_result_json = None
        self.state_manager.reset_to_initial_state()

        # Clean temporary files
        self.lifecycle_manager.cleanup_temp_files()

    def processing_finished(self, success: bool) -> None:
        """Handle the completion of PDF processing.

        Args:
            success: Whether processing completed successfully
        """
        has_text = bool(self.ui.text_edit.toPlainText().strip())
        has_json = self.current_result_json is not None

        self.worker_manager.handle_completion(
            success=success,
            has_text=has_text,
            has_json=has_json,
            current_json=self.current_result_json,
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        """Handle the window close event. Clean up resources.

        Args:
            event: Close event
        """
        self.lifecycle_manager.on_window_close(event)

    def debug_markdown(self) -> None:
        """Run a debug test of the markdown conversion directly from the UI."""
        self.update_status("Running markdown debug test...")

        result = MarkdownDebugService.run_debug_test(MAX_PREVIEW_LENGTH)

        self.format_display_manager.set_full_markdown_content(
            result.full_markdown
        )
        self.ui.markdown_preview.setPlainText(result.display_content)

        # Switch to markdown tab
        _ = self.ui.tab_widget.setCurrentIndex(1)

        # Enable save button if we have content
        if result.full_markdown:
            self.ui.save_markdown_button.setEnabled(True)

        if result.success:
            self.update_status("Markdown debug test completed")
            _ = QMessageBox.information(
                self,
                "Markdown Debug Test",
                "Markdown debug test completed. See the Markdown tab for "
                "results.",
            )
        elif result.error_message:
            self.show_error(result.error_message)
