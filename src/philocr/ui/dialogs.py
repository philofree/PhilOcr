#!/usr/bin/env python3
"""Dialog components for the application."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from philocr.ui.credentials_form_handler import CredentialsFormHandler
from philocr.ui.dialog_form_builder import DialogFormBuilder
from philocr.utils.settings_manager import get_settings_manager

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class AboutDialog(QDialog):
    """About dialog for the application."""

    def __init__(
        self,
        parent: Any | None,
        app_name: str,
        app_version: str,
        app_description: str,
        app_copyright: str,
    ) -> None:
        """Initialize the AboutDialog."""
        super().__init__(parent)
        self.setWindowTitle("About")
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        # Application title and version
        title_label = QLabel(f"{app_name} v{app_version}")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(app_description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # Copyright
        copyright_label = QLabel(app_copyright)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        # Additional information
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml(
            """
        <p>This tool processes scanned PDFs of ancient Greek texts using Google Document AI, 
        producing clean digital text ready for the Philofree corpus. It is designed to digitize 
        out-of-copyright print editions and make them available for scholarly use.</p>
        
        <p><b>Features:</b><br>
        - PDF processing with automatic handling of large scholarly editions<br>
        - Polytonic Greek support — full Unicode coverage for ancient Greek diacritics<br>
        - Multiple output formats — Text, Markdown, HTML, JSON<br>
        - Document structure identification — automatically identifies line numbers, 
        footnotes, headers, indentation levels, and references<br>
        - Memory-efficient processing — handles large critical editions efficiently<br>
        - Batch processing — process entire library collections systematically
        </p>
        
        <p><b>Libraries used:</b><br>
        - PyQt6 for user interface<br>
        - PyMuPDF for PDF handling<br>
        - Google Cloud Document AI for OCR
        </p>
        
        <p><b>Part of the Philofree Project:</b><br>
        The OCR output feeds directly into the Philofree text processing pipeline, 
        where it receives sentence segmentation with Philofree IDs, reference system 
        mapping (Stephanus, Bekker, etc.), and integration with the searchable corpus.
        </p>
        """
        )
        layout.addWidget(info_text)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        _ = button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class CredentialsDialog(QDialog):
    """Dialog for setting up Google Cloud credentials."""

    def __init__(self, parent: Any | None) -> None:
        """Initialize the CredentialsDialog."""
        super().__init__(parent)
        self.setWindowTitle("PhilOcr - Google Cloud Credentials")
        self.resize(750, 400)

        settings_manager = get_settings_manager()
        self.form_handler = CredentialsFormHandler(settings_manager)
        self.form_builder = DialogFormBuilder()

        layout = QFormLayout(self)
        self._create_input_fields(layout)
        self._add_buttons(layout)

    def _create_input_fields(self, layout: QFormLayout) -> None:
        """Create and add all input fields to the layout.

        Args:
            layout: Form layout to add fields to
        """
        current = self.form_handler.load_current_settings()

        # Create input fields using form builder
        self.project_id_input = self.form_builder.create_input_field(
            current["project_id"], "Your Google Cloud Project ID"
        )
        self.document_ai_project_id_input = self.form_builder.create_input_field(
            current["document_ai_project_id"],
            "Optional - defaults to Google Cloud Project ID above",
        )
        self.processor_id_input = self.form_builder.create_input_field(
            current["processor_id"]
        )
        self.location_input = self.form_builder.create_input_field(current["location"])
        self.credentials_path_input = self.form_builder.create_input_field(
            current["credentials_path"], min_width=350
        )

        # Add fields to layout
        layout.addRow("Google Cloud Project ID:", self.project_id_input)

        doc_ai_project_label = QLabel("Document AI Project ID:")
        doc_ai_project_label.setToolTip(
            "Optional: Leave empty to use the same as Google Cloud Project ID. "
            "Only set if your Document AI processor is in a different project."
        )
        layout.addRow(doc_ai_project_label, self.document_ai_project_id_input)

        layout.addRow("Document AI Processor ID:", self.processor_id_input)
        layout.addRow("Document AI Location:", self.location_input)

        # Add browse button for credentials file
        self.form_builder.add_file_browser_row(
            layout,
            "Credentials File:",
            self.credentials_path_input,
            self.browse_credentials_file,
        )

        # Add info label
        self.form_builder.add_info_label(
            layout, "Settings are saved securely in your user configuration directory."
        )

    def _add_buttons(self, layout: QFormLayout) -> None:
        """Add dialog buttons to the layout.

        Args:
            layout: Form layout to add buttons to
        """
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        _ = button_box.accepted.connect(self.save_and_accept)
        _ = button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def browse_credentials_file(self) -> None:
        """Open a file dialog to select a credentials file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Cloud Credentials JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            self.credentials_path_input.setText(file_path)

    def save_and_accept(self) -> None:
        """Save settings and accept the dialog."""
        settings = self.form_handler.collect_settings(
            project_id=self.project_id_input.text(),
            document_ai_project_id=self.document_ai_project_id_input.text(),
            processor_id=self.processor_id_input.text(),
            location=self.location_input.text(),
            credentials_path=self.credentials_path_input.text(),
        )

        is_valid, error_message = self.form_handler.validate_settings(settings)
        if not is_valid:
            _ = QMessageBox.warning(self, "Validation Error", error_message)
            return

        # Check if credentials file exists (but allow empty for optional)
        if settings["credentials_path"] and not os.path.exists(
            settings["credentials_path"]
        ):
            reply = QMessageBox.question(
                self,
                "File Not Found",
                f"Credentials file not found at:\n{settings['credentials_path']}\n\n"
                "Do you want to save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            self.form_handler.save_settings(settings)
            self.form_handler.set_environment_variables(settings)
            _ = QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully.\n\n"
                "You may need to restart the application for changes to take full effect.",
            )
            self.accept()
        except Exception as e:
            from philocr.utils.logging_config import get_logger

            logger = get_logger(__name__)
            logger.error(
                "settings_save_dialog_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            _ = QMessageBox.critical(
                self, "Save Error", f"Failed to save settings: {str(e)}"
            )

    def get_credentials(self) -> dict[str, str]:
        """Get the entered credentials and normalize them.

        Uses form handler to collect and normalize credentials.

        Returns:
            Normalized credentials dictionary
        """
        return self.form_handler.collect_settings(
            project_id=self.project_id_input.text(),
            document_ai_project_id=self.document_ai_project_id_input.text(),
            processor_id=self.processor_id_input.text(),
            location=self.location_input.text(),
            credentials_path=self.credentials_path_input.text(),
        )
