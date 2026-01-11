"""Configuration validation utilities.

This module provides configuration validation logic without UI dependencies,
allowing for better testability and separation of concerns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from philocr.utils.env_utils import get_google_credentials, load_env_file

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ConfigValidationResult(NamedTuple):
    """Result of configuration validation.

    Attributes:
        is_valid: Whether the configuration is valid
        missing_fields: List of missing required fields
        error_message: Error message if validation failed
    """

    is_valid: bool
    missing_fields: list[str]
    error_message: str


def validate_configuration() -> ConfigValidationResult:
    """Validate application configuration.

    Returns:
        ConfigValidationResult indicating validity and missing fields
    """
    try:
        _ = load_env_file()
        credentials = get_google_credentials()

        if not credentials:
            return ConfigValidationResult(
                is_valid=False,
                missing_fields=["credentials"],
                error_message="Google Cloud credentials not found or invalid format",
            )

        missing_fields: list[str] = []
        if not credentials.get("project_id"):
            missing_fields.append("project_id")
        if not credentials.get("processor_id"):
            missing_fields.append("processor_id")

        if missing_fields:
            return ConfigValidationResult(
                is_valid=False,
                missing_fields=missing_fields,
                error_message=f"Missing required configuration fields: {', '.join(missing_fields)}",
            )

        logger.info("configuration_validation_passed")
        return ConfigValidationResult(
            is_valid=True, missing_fields=[], error_message=""
        )

    except Exception as e:
        logger.error(
            "configuration_validation_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(f"CRITICAL: Configuration validation failed - {e}") from e


def validate_credentials(credentials: dict[str, str | None]) -> ConfigValidationResult:
    """Validate credential fields.

    Args:
        credentials: Dictionary of credential fields to validate

    Returns:
        ConfigValidationResult indicating validity and missing fields
    """
    missing_fields: list[str] = []

    # Required fields
    required_fields = ["project_id", "processor_id"]
    for field in required_fields:
        value = credentials.get(field)
        if not value or not str(value).strip():
            missing_fields.append(field)

    if missing_fields:
        return ConfigValidationResult(
            is_valid=False,
            missing_fields=missing_fields,
            error_message=f"Missing required credential fields: {', '.join(missing_fields)}",
        )

    return ConfigValidationResult(is_valid=True, missing_fields=[], error_message="")


def get_configuration_status_message(result: ConfigValidationResult) -> str:
    """Get a human-readable status message from validation result.

    Args:
        result: The validation result

    Returns:
        Human-readable status message
    """
    if result.is_valid:
        return "Configuration is valid."

    if result.missing_fields:
        fields_str = ", ".join(result.missing_fields)
        return f"Configuration incomplete. Missing: {fields_str}"

    return result.error_message or "Configuration validation failed."
