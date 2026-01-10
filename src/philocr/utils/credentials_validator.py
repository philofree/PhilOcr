"""Credentials validation utilities.

This module provides credential validation logic without UI dependencies,
specifically for validating document processing credentials.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.exceptions import CredentialsError
from philocr.utils.exceptions import FileNotFoundError as PhilOcrFileNotFoundError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def validate_credentials_file(credentials_path: str | Path) -> None:
    """Validate that a credentials file exists and is readable.

    Args:
        credentials_path: Path to the credentials file

    Raises:
        FileNotFoundError: If the credentials file does not exist
        CredentialsError: If the credentials file cannot be read
    """
    creds_path = Path(credentials_path)
    if not creds_path.exists():
        logger.error("credentials_file_not_found", file_path=str(creds_path))
        raise PhilOcrFileNotFoundError(str(creds_path))

    if not creds_path.is_file():
        logger.error("credentials_path_not_file", file_path=str(creds_path))
        raise CredentialsError(f"Credentials path is not a file: {creds_path}")

    if not creds_path.stat().st_size > 0:
        logger.error("credentials_file_empty", file_path=str(creds_path))
        raise CredentialsError(f"Credentials file is empty: {creds_path}")


def validate_credential_fields(
    project_id: str | None,
    processor_id: str | None,
    location: str | None = None,
) -> None:
    """Validate credential field values.

    Args:
        project_id: Google Cloud project ID
        processor_id: Document AI processor ID
        location: Document AI location (optional)

    Raises:
        CredentialsError: If any required field is invalid
    """
    if not project_id or not project_id.strip():
        logger.error("credentials_validation_failed", field="project_id")
        raise CredentialsError("Project ID is required and cannot be empty")

    if not processor_id or not processor_id.strip():
        logger.error("credentials_validation_failed", field="processor_id")
        raise CredentialsError("Processor ID is required and cannot be empty")

    # Location is optional but if provided should not be empty
    if location is not None and not location.strip():
        logger.warning("credentials_location_empty", field="location")
        # Location can be empty, just log a warning


def normalize_credential_dict(
    credentials: dict[str, Any],
) -> dict[str, str]:
    """Normalize and extract credential fields from a dictionary.

    Handles cases where document_ai_project_id might be used instead of project_id.

    Args:
        credentials: Dictionary containing credential fields

    Returns:
        Normalized dictionary with standard field names

    Raises:
        CredentialsError: If required fields are missing
    """
    # Handle both project_id and document_ai_project_id
    project_id = (
        credentials.get("document_ai_project_id") or credentials.get("project_id") or ""
    ).strip()

    processor_id = (credentials.get("processor_id") or "").strip()
    location = (credentials.get("location") or "us").strip()

    validate_credential_fields(project_id, processor_id, location)

    return {
        "project_id": project_id,
        "processor_id": processor_id,
        "location": location,
        "credentials_path": str(credentials.get("credentials_path", "")),
    }
