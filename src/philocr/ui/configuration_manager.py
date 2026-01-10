#!/usr/bin/env python3
"""Configuration Manager for MainWindow.

This module handles configuration checking and warnings for Google Cloud
credentials.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox, QWidget

from philocr.utils.config_validator import validate_configuration
from philocr.utils.exceptions import ConfigurationError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ConfigurationManager:
    """Manages configuration checking and warnings."""

    def __init__(
        self,
        parent_widget: QWidget,
        on_config_error: Callable[[str], None],
        on_settings_requested: Callable[[], None],
    ) -> None:
        """Initialize the Configuration Manager.

        Args:
            parent_widget: Parent widget for dialogs
            on_config_error: Callback for configuration errors
            on_settings_requested: Callback when settings dialog is requested
        """
        self.parent_widget = parent_widget
        self.on_config_error = on_config_error
        self.on_settings_requested = on_settings_requested

    def check(self) -> None:
        """Check if the application is properly configured."""
        try:
            validation_result = validate_configuration()

            if not validation_result.is_valid:
                logger.warning(
                    "configuration_validation_failed",
                    missing_fields=validation_result.missing_fields,
                    error_message=validation_result.error_message,
                )
                self.show_warning()
        except ConfigurationError as e:
            logger.error(
                "configuration_check_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.on_config_error(f"Configuration error: {e}")
        except Exception as e:
            logger.error(
                "configuration_check_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.on_config_error(f"Unexpected configuration error: {e}")

    def show_warning(self) -> None:
        """Show a warning if the application is not properly configured."""
        msg = QMessageBox(self.parent_widget)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("PhilOcr - Configuration Missing")
        msg.setText(
            "The application is not properly configured to use Google Document AI."
        )
        msg.setInformativeText(
            "To use this application, you need to set up your Google Cloud credentials."
        )
        msg.setDetailedText(
            "Required configuration:\n"
            "- GOOGLE_CLOUD_PROJECT_ID: Your Google Cloud project ID\n"
            "- DOCUMENT_AI_PROCESSOR_ID: Your Document AI processor ID\n"
            "- GOOGLE_APPLICATION_CREDENTIALS: Path to your credentials JSON file\n\n"
            "Click 'Configure' to open the settings dialog, or create an ENV.local "
            "file based on the ENV.template file."
        )
        configure_button = msg.addButton("Configure", QMessageBox.ButtonRole.AcceptRole)
        assert configure_button is not None
        _ = msg.addButton("OK", QMessageBox.ButtonRole.RejectRole)
        _ = msg.exec()

        if msg.clickedButton() == configure_button:
            self.on_settings_requested()
