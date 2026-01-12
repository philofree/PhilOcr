"""Configuration path resolution utilities.

This module provides platform-specific path resolution for configuration files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class ConfigPathResolver:
    """Resolves configuration directory paths for different platforms."""

    @staticmethod
    def get_config_directory() -> Path:
        """Get the user configuration directory based on platform.

        Returns:
            Path to the configuration directory
        """
        if os.name == "nt":  # Windows
            return Path(os.getenv("APPDATA", "")) / "PhilOcr"
        if sys.platform == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "PhilOcr"
        # Linux and others
        return Path.home() / ".config" / "philocr"

    @staticmethod
    def ensure_config_dir(config_dir: Path) -> None:
        """Ensure the configuration directory exists.

        Args:
            config_dir: Path to configuration directory

        Raises:
            RuntimeError: If directory creation fails
        """
        from philocr.utils.logging_config import get_logger

        logger = get_logger(__name__)

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions on the config directory
            if os.name != "nt":  # Unix-like systems
                os.chmod(config_dir, 0o700)
            return True
        except PermissionError as e:
            logger.error(
                "config_dir_create_permission_denied",
                config_dir=str(config_dir),
                error=str(e),
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Config directory creation permission denied - {e}"
            ) from e
        except Exception as e:
            logger.error(
                "config_dir_create_failed",
                config_dir=str(config_dir),
                error=str(e),
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Config directory creation failed - {e}"
            ) from e
