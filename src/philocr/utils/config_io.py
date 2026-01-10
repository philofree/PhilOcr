"""Configuration file I/O operations.

This module handles loading and saving configuration files
in YAML or JSON format with automatic format detection.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Try to import yaml, with graceful fallback to JSON if not available
_yaml_module: Any | None = None
_yaml_available: bool = False

try:
    import yaml

    _yaml_module = yaml
    _yaml_available = True
except ImportError:
    _yaml_available = False
    if not TYPE_CHECKING:
        logger.warning(
            "yaml_not_available",
            fallback="json",
            suggestion="Install PyYAML for better configuration file readability: pip install pyyaml",
        )

YAML_AVAILABLE = _yaml_available


class ConfigIO:
    """Handles configuration file I/O operations."""

    @staticmethod
    def detect_config_file(config_dir: Path) -> Path:
        """Detect which config file exists (YAML or JSON).

        Args:
            config_dir: Configuration directory path

        Returns:
            Path to existing config file, or YAML path if neither exists
        """
        yaml_file = config_dir / "config.yaml"
        json_file = config_dir / "config.json"

        if yaml_file.exists():
            return yaml_file
        if json_file.exists():
            return json_file

        # Default to YAML if available, otherwise JSON
        return yaml_file if YAML_AVAILABLE else json_file

    @staticmethod
    def load_from_file(config_file: Path) -> dict[str, Any]:
        """Load configuration from a file.

        Args:
            config_file: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not config_file.exists():
            logger.debug("config_file_not_found", config_file=str(config_file))
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_file, encoding="utf-8") as f:
                if config_file.suffix == ".yaml" or config_file.suffix == ".yml":
                    if not YAML_AVAILABLE:
                        raise ValueError(
                            "YAML file detected but PyYAML is not installed"
                        )
                    if _yaml_module is None:
                        raise ValueError(
                            "YAML module not available despite YAML_AVAILABLE being True"
                        )
                    return _yaml_module.safe_load(f) or {}
                else:
                    import json

                    return json.load(f)
        except Exception as e:
            logger.error(
                "config_file_load_failed",
                config_file=str(config_file),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise ValueError(f"Failed to load configuration file: {e}") from e

    @staticmethod
    def save_to_file(config: dict[str, Any], config_file: Path) -> bool:
        """Save configuration to a file.

        Args:
            config: Configuration dictionary to save
            config_file: Path to configuration file

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w", encoding="utf-8") as f:
                if config_file.suffix == ".yaml" or config_file.suffix == ".yml":
                    if not YAML_AVAILABLE:
                        logger.warning(
                            "yaml_not_available_fallback_json",
                            config_file=str(config_file),
                        )
                        import json

                        json.dump(config, f, indent=2)
                    else:
                        if _yaml_module is None:
                            raise ValueError(
                                "YAML module not available despite YAML_AVAILABLE being True"
                            )
                        _yaml_module.dump(
                            config,
                            f,
                            default_flow_style=False,
                            allow_unicode=True,
                        )
                else:
                    import json

                    json.dump(config, f, indent=2)

            logger.info("config_file_saved", config_file=str(config_file))
            return True
        except Exception as e:
            logger.error(
                "config_file_save_failed",
                config_file=str(config_file),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return False
