#!/usr/bin/env python3
"""Main application window for the OJD OCR app."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStatusBar

from philocr.ui.dialog_manager import DialogManager
from philocr.ui.lifecycle_manager import LifecycleManager
from philocr.ui.main_window_coordinator import MainWindowCoordinator
from philocr.ui.main_window_factory import MainWindowManagerFactory
from philocr.ui.main_window_state_manager import MainWindowStateManager
from philocr.ui.ui_builder import UICallbacks
from philocr.ui.ui_composer import MainWindowUIComposer
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
            on_pipeline_config=self.show_pipeline_config_dialog,
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
        self.file_operations_manager = factory.create_file_operations_manager(
            parent_widget=self,
            current_result_json_getter=lambda: self.current_result_json,
            current_result_json_setter=lambda x: setattr(
                self, "current_result_json", x
            ),
            format_display_manager=self.format_display_manager,
            on_status_update=self.update_status,
            on_save_buttons_enable=(self.state_manager.enable_save_buttons),
        )
        self.worker_manager = factory.create_worker_manager(
            temp_cleaner=self.temp_cleaner,
            progress_bar=self.ui.progress_bar,
            stage_progress_widget=self.ui.stage_progress,
            on_text_update=self.update_text,
            on_status_update=self.update_status,
            on_error=self.show_error,
            on_finished=self.processing_finished,
            on_json_ready=self.json_data_ready,
            on_button_state_change=self.state_manager.set_button_states,
            on_preview_clear=self.state_manager.clear_previews,
            on_stage_progress=self._handle_stage_progress,
            on_overall_progress=self._handle_overall_progress,
            on_template_ready=self._handle_template_ready,
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

    def show_pipeline_config_dialog(self) -> None:
        """Show the pipeline configuration dialog."""
        self.dialog_manager.show_pipeline_config()

    def select_file(self) -> None:
        """Handle file selection for a single PDF."""
        file_path = self.file_operations_manager.select_single_file()
        if file_path:
            processing_mode = self._get_processing_mode()
            self.worker_manager.start_single_file_processing(
                file_path, processing_mode=processing_mode
            )

    def select_multiple_files(self) -> None:
        """Handle selection of multiple PDF files for batch processing."""
        file_paths = self.file_operations_manager.select_multiple_files()
        if file_paths:
            processing_mode = self._get_processing_mode()
            self.worker_manager.start_batch_processing(
                file_paths, processing_mode=processing_mode
            )

    def _get_processing_mode(self) -> str:
        """Get the selected processing mode from UI.

        Returns:
            "standard" or "advanced_pipeline"
        """
        if (
            hasattr(self.ui, "pipeline_mode_radio")
            and self.ui.pipeline_mode_radio.isChecked()
        ):
            return "advanced_pipeline"
        return "standard"

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

    def _handle_stage_progress(
        self, stage_name: str, progress: int, status_text: str
    ) -> None:
        """Handle stage-specific progress updates.

        Args:
            stage_name: Stage name
            progress: Progress percentage (0-100)
            status_text: Status message
        """
        if hasattr(self.ui, "stage_progress"):
            self.ui.stage_progress.update_stage(stage_name, progress, status_text)

    def _handle_overall_progress(self, progress: int) -> None:
        """Handle overall progress updates.

        Args:
            progress: Overall progress percentage (0-100)
        """
        if hasattr(self.ui, "stage_progress"):
            self.ui.stage_progress.update_overall(progress)
        # Also update standard progress bar for compatibility
        if hasattr(self.ui, "progress_bar"):
            self.ui.progress_bar.setValue(progress)

    def _handle_template_ready(self, template_dict: dict[str, Any]) -> None:
        """Handle template ready signal.

        Args:
            template_dict: Template metadata dictionary
        """
        if hasattr(self.ui, "template_preview") and self.ui.template_preview:
            # Format template information for display
            template_text = self._format_template_preview(template_dict)
            self.ui.template_preview.setPlainText(template_text)

    def _format_template_preview(self, template_dict: dict[str, Any]) -> str:
        """Format template information for preview display.

        Args:
            template_dict: Template metadata dictionary

        Returns:
            Formatted template preview text
        """
        body_bounds = template_dict.get("body_bounds", {})
        lines = [
            "Template Preview",
            "=" * 50,
            "",
            f"Confidence: {template_dict.get('confidence', 0.0):.2f}",
            f"Pages Analysed: {template_dict.get('pages_analysed', 0)}",
            "",
            "Body Region:",
            f"  Left: {body_bounds.get('left', 0)}",
            f"  Right: {body_bounds.get('right', 0)}",
            f"  Top: {body_bounds.get('top', 0)}",
            f"  Bottom: {body_bounds.get('bottom', 0)}",
            "",
            "Page Dimensions:",
            f"  Width: {template_dict.get('page_width', 0)}",
            f"  Height: {template_dict.get('page_height', 0)}",
            "",
            "Zone Boundaries:",
            f"  Header Bottom: {template_dict.get('header_bottom', 0)}",
            f"  Footer Top: {template_dict.get('footer_top', 0)}",
            f"  Left Margin Right: {template_dict.get('left_margin_right', 0)}",
            f"  Right Margin Left: {template_dict.get('right_margin_left', 0)}",
            "",
            "Features:",
            f"  Line Numbers (Left): {template_dict.get('has_line_numbers_left', False)}",
            f"  Line Numbers (Right): {template_dict.get('has_line_numbers_right', False)}",
            f"  Footnotes: {template_dict.get('has_footnotes', False)}",
            "",
            "Note: Visual overlay can be generated using the template visualizer.",
        ]
        return "\n".join(lines)

    def debug_markdown(self) -> None:
        """Run a debug test of the markdown conversion directly from the UI."""
        self.update_status("Running markdown debug test...")

        result = MarkdownDebugService.run_debug_test(MAX_PREVIEW_LENGTH)

        self.format_display_manager.set_full_markdown_content(result.full_markdown)
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
                "Markdown debug test completed. See the Markdown tab for " "results.",
            )
        elif result.error_message:
            self.show_error(result.error_message)
