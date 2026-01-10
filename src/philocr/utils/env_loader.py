#!/usr/bin/env python3
"""Environment variable loader for embedded configuration.

This module handles loading environment variables from embedded configuration data
in the packaged application.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Empty placeholder for embedded environment variables
# Should be populated from secure sources at runtime, not hardcoded
EMBEDDED_ENV: dict[str, str] = {}


def load_embedded_env() -> None:
    """
    Load embedded environment variables if available.

    This function should load credentials from a secure source like:
    - Environment variables
    - A credentials file outside the codebase
    - A secure credential store

    It should NOT contain hardcoded credentials.
    """
    try:
        logger.info("embedded_env_loading_started")
        if EMBEDDED_ENV:
            for key, value in EMBEDDED_ENV.items():
                os.environ[key] = value
                logger.debug("env_var_set", key=key, has_value=bool(value))
            logger.info(
                "embedded_env_loaded",
                variable_count=len(EMBEDDED_ENV),
            )
        else:
            logger.info("embedded_env_empty")

    except Exception as e:
        logger.error(
            "embedded_env_load_error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        flush_loggers()
        raise


def get_embedded_env() -> dict[str, Any] | None:
    """
    Retrieve the embedded environment variables if available.

    Returns:
        Optional[Dict[str, Any]]: The embedded environment variables or None if not found.
    """
    try:
        env_vars = {}
        # List of environment variables to embed
        env_keys = [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_CLOUD_PROJECT_ID",
            "DOCUMENT_AI_PROJECT_ID",
            "DOCUMENT_AI_PROCESSOR_ID",
            "DOCUMENT_AI_LOCATION",
            "GOOGLE_CLIENT_EMAIL",
            "GOOGLE_PRIVATE_KEY",
            "GOOGLE_PRIVATE_KEY_ID",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_AUTH_URI",
            "GOOGLE_TOKEN_URI",
            "GOOGLE_AUTH_PROVIDER_CERT_URL",
            "GOOGLE_CLIENT_CERT_URL",
        ]

        for key in env_keys:
            if key in os.environ:
                env_vars[key] = os.environ[key]
                logger.debug("env_var_found", key=key)
            else:
                logger.warning("env_var_not_found", key=key)

        logger.info(
            "embedded_env_collected",
            variable_count=len(env_vars),
            total_checked=len(env_keys),
        )
        return env_vars

    except Exception as e:
        logger.error(
            "embedded_env_get_error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        flush_loggers()
        raise
