"""Credentials form data handling.

This module handles the business logic for credentials dialog forms,
separating data collection, validation, and persistence from UI concerns.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class CredentialsFormHandler:
    """Handles credentials form data operations."""

    def __init__(self, settings_manager: Any) -> None:
        """Initialize the form handler.

        Args:
            settings_manager: Settings manager instance
        """
        self.settings_manager = settings_manager

    def load_current_settings(self) -> dict[str, str]:
        """Load current settings from manager and environment.

        Returns:
            Dictionary of current setting values
        """
        settings = self.settings_manager.load_settings()
        return {
            "project_id": (
                settings.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
            ),
            "document_ai_project_id": (
                settings.get("document_ai_project_id")
                or os.getenv("DOCUMENT_AI_PROJECT_ID", "")
            ),
            "processor_id": (
                settings.get("processor_id")
                or os.getenv("DOCUMENT_AI_PROCESSOR_ID", "")
            ),
            "location": (
                settings.get("location") or os.getenv("DOCUMENT_AI_LOCATION", "us")
            ),
            "credentials_path": (
                settings.get("credentials_path")
                or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
            ),
        }

    def collect_settings(
        self,
        project_id: str,
        document_ai_project_id: str,
        processor_id: str,
        location: str,
        credentials_path: str,
    ) -> dict[str, str]:
        """Collect and normalize settings from input values.

        Args:
            project_id: Google Cloud Project ID
            document_ai_project_id: Document AI Project ID (may be empty)
            processor_id: Processor ID
            location: Location
            credentials_path: Path to credentials file

        Returns:
            Normalized settings dictionary
        """
        credentials_path_abs = (
            os.path.abspath(credentials_path.strip())
            if credentials_path.strip()
            else ""
        )

        project_id_clean = project_id.strip()
        document_ai_project_id_clean = document_ai_project_id.strip()

        # If Document AI Project ID is empty, use Google Cloud Project ID
        if not document_ai_project_id_clean:
            document_ai_project_id_clean = project_id_clean

        return {
            "project_id": project_id_clean,
            "document_ai_project_id": document_ai_project_id_clean,
            "processor_id": processor_id.strip(),
            "location": location.strip(),
            "credentials_path": credentials_path_abs,
        }

    def validate_settings(self, settings: dict[str, str]) -> tuple[bool, str]:
        """Validate that required settings are provided.

        Args:
            settings: Settings dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not settings["project_id"]:
            return False, "Google Cloud Project ID is required."

        if not settings["processor_id"]:
            return False, "Document AI Processor ID is required."

        if not settings["location"]:
            return False, "Document AI Location is required."

        if not settings["credentials_path"]:
            return False, "Credentials file path is required."

        return True, ""

    def save_settings(self, settings: dict[str, str]) -> bool:
        """Save settings to persistent storage.

        Args:
            settings: Settings dictionary to save

        Returns:
            True if save was successful
        """
        try:
            self.settings_manager.save_settings(settings)
            logger.info("credentials_settings_saved")
            return True
        except Exception as e:
            logger.error(
                "credentials_save_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return False

    def set_environment_variables(self, settings: dict[str, str]) -> None:
        """Set environment variables from settings.

        Args:
            settings: Settings dictionary
        """
        os.environ["GOOGLE_CLOUD_PROJECT_ID"] = settings["project_id"]
        os.environ["DOCUMENT_AI_PROJECT_ID"] = settings["document_ai_project_id"]
        os.environ["DOCUMENT_AI_PROCESSOR_ID"] = settings["processor_id"]
        os.environ["DOCUMENT_AI_LOCATION"] = settings["location"]

        if settings["credentials_path"]:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings["credentials_path"]
