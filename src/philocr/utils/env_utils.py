"""
Environment utilities for the PhilOcr application.
This module provides functions for loading environment variables from .env files
and handling credentials securely.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def load_env_file(file_path: str = "ENV.local") -> dict[str, str | None]:
    """
    Load environment variables from a file and set them in the current process.
    Also loads from user settings if available.

    Args:
        file_path (str): Path to the environment file (default: "ENV.local")

    Returns:
        dict[str, Optional[str]]: Dictionary of loaded environment variables
    """
    env_vars: dict[str, str | None] = {}

    # First, try to load from user settings
    try:
        from philocr.utils.settings_manager import get_settings_manager

        settings_manager = get_settings_manager()
        user_settings = settings_manager.load_settings()

        # Map settings keys to environment variable names
        setting_mapping = {
            "project_id": "GOOGLE_CLOUD_PROJECT_ID",
            "processor_id": "DOCUMENT_AI_PROCESSOR_ID",
            "location": "DOCUMENT_AI_LOCATION",
            "credentials_path": "GOOGLE_APPLICATION_CREDENTIALS",
        }

        for setting_key, env_key in setting_mapping.items():
            if setting_key in user_settings and user_settings[setting_key]:
                setting_value = user_settings[setting_key]
                if setting_value is not None:
                    env_vars[env_key] = setting_value
                    os.environ[env_key] = setting_value
                    logger.info(
                        "env_var_loaded_from_settings",
                        env_key=env_key,
                        source="user_settings",
                    )

        # Set DOCUMENT_AI_PROJECT_ID from document_ai_project_id if available,
        # otherwise fall back to project_id
        document_ai_project_id = user_settings.get("document_ai_project_id")
        if not document_ai_project_id and "project_id" in user_settings:
            document_ai_project_id = user_settings["project_id"]

        if document_ai_project_id:
            env_vars["DOCUMENT_AI_PROJECT_ID"] = document_ai_project_id
            os.environ["DOCUMENT_AI_PROJECT_ID"] = document_ai_project_id
            logger.info(
                "env_var_loaded_from_settings",
                env_key="DOCUMENT_AI_PROJECT_ID",
                source="user_settings",
            )

    except Exception as e:
        logger.warning(
            "user_settings_load_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

    # Then try to load from ENV.local file (for backward compatibility).
    # IMPORTANT: ENV.local should be treated as a fallback and must NOT override
    # values already loaded from user settings or the process environment.
    # Try to find the file in multiple locations
    paths_to_check = []

    # First try the provided path as is
    paths_to_check.append(Path(file_path))

    # Check in the current directory
    paths_to_check.append(Path.cwd() / file_path)

    # Check in the script's directory
    if getattr(sys, "frozen", False):
        # We're running in a PyInstaller bundle
        app_dir = Path(sys._MEIPASS)  # type: ignore
        paths_to_check.append(app_dir / file_path)
    else:
        # We're running in normal Python environment
        script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        paths_to_check.append(script_dir / file_path)
        # Try one level up from script directory
        paths_to_check.append(script_dir.parent / file_path)

    env_file_found = False
    # Keys already loaded from user settings (or otherwise set earlier in this
    # function) should not be overridden by ENV.local.
    preloaded_keys = set(env_vars.keys())

    for path in paths_to_check:
        if path.exists():
            try:
                logger.info(
                    "env_file_found",
                    file_path=str(path),
                )
                # Open and read the file
                with open(path) as file:
                    for line in file:
                        line = line.strip()

                        # Skip empty lines and comments
                        if not line or line.startswith("#"):
                            continue

                        # Parse the key-value pair
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Remove quotes if present
                            if (value.startswith('"') and value.endswith('"')) or (
                                value.startswith("'") and value.endswith("'")
                            ):
                                value = value[1:-1]

                            # Store in our dictionary and set as environment variable
                            # only if we haven't already loaded a value from settings.
                            if key in preloaded_keys:
                                continue
                            env_vars[key] = value
                            os.environ[key] = value

                logger.info(
                    "env_vars_loaded_from_file",
                    file_path=str(path),
                    var_count=len(env_vars),
                )
                env_file_found = True
                break
            except Exception as e:
                logger.error(
                    "env_file_load_failed",
                    file_path=str(path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

    if not env_file_found:
        logger.warning(
            "env_file_not_found",
            file_path=file_path,
            checked_paths=[str(p) for p in paths_to_check],
        )

    # Check for embedded credentials JSON in packaged app
    if (
        getattr(sys, "frozen", False)
        and "GOOGLE_APPLICATION_CREDENTIALS" not in env_vars
    ):
        # Try to find bundled credentials file
        bundled_creds = find_bundled_credentials()
        if bundled_creds:
            env_vars["GOOGLE_APPLICATION_CREDENTIALS"] = bundled_creds
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = bundled_creds

    # Log important configuration details for debugging, but mask sensitive values
    log_env_var("DOCUMENT_AI_PROJECT_ID", env_vars)
    log_env_var("DOCUMENT_AI_LOCATION", env_vars)
    log_env_var("DOCUMENT_AI_PROCESSOR_ID", env_vars)

    # Check for critical environment variables
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning(
            "critical_env_var_missing",
            env_var="GOOGLE_APPLICATION_CREDENTIALS",
            impact="document_ai_may_not_function",
        )

    return env_vars


def log_env_var(name: str, env_vars: dict[str, str | None]) -> None:
    """
    Safely log an environment variable without exposing sensitive data.

    Args:
        name (str): Name of the environment variable
        env_vars (dict[str, Optional[str]]): Dictionary of environment variables
    """
    value = os.getenv(name)
    if value:
        # For sensitive variables like keys, don't log the actual value
        if "KEY" in name or "SECRET" in name or "PASSWORD" in name or "CRED" in name:
            logger.info(
                "env_var_checked",
                env_var=name,
                is_set=True,
                value_redacted=True,
            )
        else:
            logger.info(
                "env_var_checked",
                env_var=name,
                is_set=True,
                value=value,
            )
    else:
        logger.warning(
            "env_var_not_set",
            env_var=name,
        )


def get_google_credentials() -> dict[str, str | None]:
    """
    Get Google Cloud credentials information from environment variables.
    If in a packaged application, may extract credentials to a temporary file.

    Returns:
        dict[str, Optional[str]]: Dictionary with credential information including:
            - credentials_path: Path to credentials file
            - project_id: Google Cloud project ID
            - processor_id: Document AI processor ID
            - location: Document AI location
    """
    creds_dict: dict[str, str | None] = {
        "credentials_path": None,
        "project_id": os.getenv(
            "DOCUMENT_AI_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        ),
        "processor_id": os.getenv("DOCUMENT_AI_PROCESSOR_ID"),
        "location": os.getenv("DOCUMENT_AI_LOCATION", "us"),
    }

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        # Try to find bundled credentials as fallback
        creds_path = find_bundled_credentials()
        if creds_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        else:
            logger.error(
                "credentials_env_var_not_set",
                env_var="GOOGLE_APPLICATION_CREDENTIALS",
            )

    # Set the credentials path in our dictionary (even if file doesn't exist)
    creds_dict["credentials_path"] = creds_path

    if creds_path and not os.path.exists(creds_path):
        logger.error(
            "credentials_file_not_found",
            credentials_path=creds_path,
        )
        # Keep the path in the dict even if file doesn't exist
        # The calling code can decide how to handle missing files

    return creds_dict


def find_bundled_credentials() -> str | None:
    """
    Find bundled credentials in the packaged application.
    If found, extract to a temporary file for use.

    Returns:
        str: Path to extracted credentials or None if not found
    """
    if getattr(sys, "frozen", False):
        # We're running in a PyInstaller bundle
        app_dir = Path(sys._MEIPASS)  # type: ignore

        # Try to find the bundled JSON credentials file
        # Use generic filename instead of hardcoded one
        for cred_filename in [
            "google_credentials.json",
            "credentials.json",
        ]:
            cred_path = app_dir / cred_filename
            if cred_path.exists():
                return str(cred_path)

        # If no credential file is found, try to create one from ENV.local
        env_path = app_dir / "ENV.local"
        if env_path.exists():
            try:
                # Extract credentials from ENV.local
                creds = {}
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if (value.startswith('"') and value.endswith('"')) or (
                                value.startswith("'") and value.endswith("'")
                            ):
                                value = value[1:-1]

                            if key.startswith("GOOGLE_"):
                                creds[key.replace("GOOGLE_", "").lower()] = value

                # If we have enough credentials info, create a JSON file
                if "client_email" in creds and "private_key" in creds:
                    # Create a temp file for the credentials
                    temp_dir = tempfile.gettempdir()
                    cred_file = os.path.join(temp_dir, "google_credentials_temp.json")

                    # Format the credentials JSON
                    cred_data = {
                        "type": "service_account",
                        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
                        "private_key_id": creds.get("private_key_id", ""),
                        "private_key": creds.get("private_key", ""),
                        "client_email": creds.get("client_email", ""),
                        "client_id": creds.get("client_id", ""),
                        "auth_uri": creds.get(
                            "auth_uri", "https://accounts.google.com/o/oauth2/auth"
                        ),
                        "token_uri": creds.get(
                            "token_uri", "https://oauth2.googleapis.com/token"
                        ),
                        "auth_provider_x509_cert_url": creds.get(
                            "auth_provider_cert_url",
                            "https://www.googleapis.com/oauth2/v1/certs",
                        ),
                        "client_x509_cert_url": creds.get("client_cert_url", ""),
                    }

                    with open(cred_file, "w") as f:
                        json.dump(cred_data, f)

                    logger.info(
                        "temporary_credentials_file_created",
                        credentials_path=cred_file,
                        source="env_local",
                    )
                    return cred_file

            except Exception as e:
                logger.error(
                    "credentials_creation_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

    return None
