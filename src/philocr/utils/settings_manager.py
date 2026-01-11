#!/usr/bin/env python3
"""Settings manager for storing user credentials securely."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class SettingsManager:
    """Manages application settings stored in user config directory."""

    def __init__(self) -> None:
        """Initialize the settings manager."""
        super().__init__()
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / "settings.json"
        _ = self._ensure_config_dir()

    def _get_config_directory(self) -> Path:
        """
        Get the user configuration directory.

        Returns:
            Path: Path to the configuration directory
        """
        if os.name == "nt":  # Windows
            config_dir = Path(os.getenv("APPDATA", "")) / "PhilOcr"
        elif sys.platform == "darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "PhilOcr"
        else:  # Linux and others
            config_dir = Path.home() / ".config" / "philocr"

        return config_dir

    def _ensure_config_dir(self) -> None:
        """
        Ensure the configuration directory exists.

        Raises:
            RuntimeError: If directory creation fails
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions on the config directory
            if os.name != "nt":  # Unix-like systems
                os.chmod(self.config_dir, 0o700)
            return True
        except PermissionError as e:
            logger.error(
                "config_dir_create_permission_denied",
                config_dir=str(self.config_dir),
                error=str(e),
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Settings config directory creation permission denied - {e}"
            ) from e
        except Exception as e:
            logger.error(
                "config_dir_create_failed",
                config_dir=str(self.config_dir),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Settings config directory creation failed - {e}"
            ) from e

    def load_settings(self) -> dict[str, str | None]:
        """
        Load settings from the configuration file.

        Returns:
            dict[str, Optional[str]]: Dictionary of settings
        """
        settings: dict[str, str | None] = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    settings = json.load(f)
                logger.info("settings_loaded", config_file=str(self.config_file))
            except json.JSONDecodeError as e:
                logger.error(
                    "settings_load_json_error",
                    config_file=str(self.config_file),
                    error=str(e),
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Settings file is malformed JSON - {e}"
                ) from e
            except PermissionError as e:
                logger.error(
                    "settings_load_permission_denied",
                    config_file=str(self.config_file),
                    error=str(e),
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Settings file permission denied - {e}"
                ) from e
            except Exception as e:
                logger.error(
                    "settings_load_failed",
                    config_file=str(self.config_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(f"CRITICAL: Settings load failed - {e}") from e
        else:
            logger.info("settings_file_not_found", using_defaults=True)
        return settings

    def save_settings(self, settings: dict[str, str]) -> None:
        """
        Save settings to the configuration file.

        Args:
            settings: Dictionary of settings to save

        Raises:
            RuntimeError: If save operation fails
        """
        try:
            # Ensure config directory exists
            try:
                self._ensure_config_dir()
            except Exception as e:
                logger.error(
                    "settings_save_config_dir_failed",
                    config_dir=str(self.config_dir),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Settings config directory creation failed during save - {e}"
                ) from e

            # Set restrictive file permissions
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)

            # Set restrictive permissions on the file (Unix-like systems)
            if os.name != "nt":
                os.chmod(self.config_file, 0o600)

            logger.info("settings_saved", config_file=str(self.config_file))
        except PermissionError as e:
            logger.error(
                "settings_save_permission_denied",
                config_file=str(self.config_file),
                error=str(e),
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Settings save permission denied - {e}"
            ) from e
        except OSError as e:
            logger.error(
                "settings_save_os_error",
                config_file=str(self.config_file),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Settings save OS error - {e}") from e
        except Exception as e:
            logger.error(
                "settings_save_failed",
                config_file=str(self.config_file),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Settings save failed - {e}") from e

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """
        Get a specific setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Optional[str]: Setting value or default
        """
        settings = self.load_settings()
        return settings.get(key, default)

    def set_setting(self, key: str, value: str) -> None:
        """
        Set a specific setting value.

        Args:
            key: Setting key
            value: Setting value

        Raises:
            RuntimeError: If save operation fails
        """
        settings = self.load_settings()
        settings[key] = value
        # Filter out None values before saving
        filtered_settings: dict[str, str] = {
            k: v for k, v in settings.items() if v is not None
        }
        self.save_settings(filtered_settings)


# Global settings manager instance
_settings_manager: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    """
    Get the global settings manager instance.

    Returns:
        SettingsManager: The settings manager instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
