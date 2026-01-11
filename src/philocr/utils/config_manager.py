#!/usr/bin/env python3
"""Configuration manager for storing application settings in YAML format."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.config_io import YAML_AVAILABLE, ConfigIO
from philocr.utils.config_path_resolver import ConfigPathResolver
from philocr.utils.exceptions import ConfigurationError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration stored in YAML (or JSON fallback) format."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self.config_dir = ConfigPathResolver.get_config_directory()
        self.config_file_yaml = self.config_dir / "config.yaml"
        self.config_file_json = self.config_dir / "config.json"
        self._config_loaded: dict[str, Any] | None = None
        _ = ConfigPathResolver.ensure_config_dir(self.config_dir)

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
                f"CRITICAL: Config directory creation permission denied - {e}"
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
                f"CRITICAL: Config directory creation failed - {e}"
            ) from e

    def _get_config_file(self) -> Path:
        """
        Get the appropriate config file path based on availability.

        Returns:
            Path: Path to the config file (YAML preferred, JSON fallback)
        """
        if YAML_AVAILABLE:
            # Prefer YAML if available
            if self.config_file_yaml.exists():
                return self.config_file_yaml
            # Check if JSON exists (migration scenario)
            if self.config_file_json.exists():
                return self.config_file_json
            # Default to YAML for new configs
            return self.config_file_yaml
        else:
            # Use JSON if YAML not available
            return self.config_file_json

    def load_config(self) -> dict[str, Any]:
        """Load configuration from the config file.

        Returns:
            Dictionary of configuration settings with defaults merged
        """
        if self._config_loaded is not None:
            return self._config_loaded

        config_file = self._get_config_file()
        config = self.get_default_config()

        if config_file.exists():
            try:
                file_config = ConfigIO.load_from_file(config_file)
                config.update(file_config)
                logger.info("config_loaded", config_file=str(config_file))
            except FileNotFoundError as e:
                # File was deleted between exists() check and open()
                # This is a race condition - fail fast per doctrine
                logger.error(
                    "config_file_deleted_during_load",
                    config_file=str(config_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise ConfigurationError(
                    f"Configuration file was deleted during load: {config_file}"
                ) from e
            except ValueError as e:
                # Malformed config file - fail fast per doctrine
                logger.critical(
                    "config_file_malformed_CRITICAL",
                    config_file=str(config_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise ConfigurationError(
                    f"Configuration file is malformed: {config_file}. Error: {e}"
                ) from e
        else:
            # Missing config file - fail fast per doctrine
            logger.error(
                "config_file_not_found",
                config_file=str(config_file),
                exc_info=False,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise ConfigurationError(
                f"Configuration file not found: {config_file}. "
                "Please create a configuration file before running the application."
            )

        self._config_loaded = config
        return config

    def save_config(self, config: dict[str, Any]) -> bool:
        """Save configuration to the config file.

        Args:
            config: Dictionary of configuration settings to save

        Returns:
            True if successful, False otherwise
        """
        try:
            ConfigPathResolver.ensure_config_dir(self.config_dir)
        except Exception as e:
            logger.error(
                "config_save_directory_failed",
                config_dir=str(self.config_dir),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Config directory creation failed during save - {e}"
            ) from e

        config_file = self._get_config_file()
        ConfigIO.save_to_file(config, config_file)

        if os.name != "nt":
            # Set restrictive permissions on the file (Unix-like systems)
            try:
                os.chmod(config_file, 0o600)
            except Exception as e:
                logger.error(
                    "config_file_permissions_failed",
                    config_file=str(config_file),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Config file permissions failed - {e}"
                ) from e

        self._config_loaded = config
        return True

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation (e.g., 'processing.max_pages').

        Args:
            key: Configuration key, supports dot notation for nested keys
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self.load_config()
        keys = key.split(".")
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError) as e:
            logger.error(
                "config_key_not_found_using_default",
                key=key,
                default_value=default,
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Configuration key '{key}' not found and no valid default provided"
            ) from e

    def set_config(self, key: str, value: Any) -> bool:
        """
        Set a specific configuration value using dot notation.

        Args:
            key: Configuration key, supports dot notation for nested keys
            value: Value to set

        Returns:
            bool: True if successful, False otherwise
        """
        config = self.load_config()
        keys = key.split(".")
        target = config

        # Navigate to the parent dict, creating nested dicts as needed
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        # Set the value
        target[keys[-1]] = value

        return self.save_config(config)

    @staticmethod
    def get_default_config() -> dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            dict[str, Any]: Dictionary of default configuration values
        """
        return {
            # Processing Settings
            "processing": {
                "max_pages_per_request": 15,  # Google Document AI limit
                "include_layout_info": True,  # Include layout information
                "rate_limit_requests_per_minute": 15,  # API rate limit
                "rate_limit_window_seconds": 60,  # Rate limit window
                "processing_mode": "standard",  # "standard" | "advanced_pipeline"
            },
            # Pipeline Configuration (for advanced_pipeline mode)
            "pipeline": {
                "stage1": {
                    "target_dpi": 300,
                    "output_format": "PNG",
                    "deskew_threshold": 0.1,
                },
                "stage2a": {
                    "header_search_percent": 0.15,
                    "footer_search_percent": 0.15,
                    "margin_search_percent": 0.20,
                    "content_threshold": 0.05,
                    "min_gap_size": 20,
                    "margin_smooth_sigma": 5.0,
                    "transition_threshold": 0.5,
                    "margin_default_percent": 0.05,
                    "footnote_search_percent": 0.40,
                    "horizontal_rule_min_width": 0.2,
                    "footnote_gap_min_size": 30,
                },
                "stage2b": {
                    "template_sample_size": 20,
                    "template_min_pages": 5,
                    "template_skip_first": 2,
                    "template_skip_last": 2,
                    "outlier_threshold": 2.0,
                },
                "stage2c": {
                    "use_cropping": False,
                    "crop_padding": 0,
                },
                "stage3": {
                    "ocr_max_retries": 3,
                    "ocr_retry_backoff_base": 2.0,
                    "ocr_rate_limit_per_minute": 15,
                },
                "stage4": {
                    "indent_ratio_threshold_1": 0.02,
                    "indent_ratio_threshold_2": 0.06,
                    "verse_avg_line_threshold": 60,
                    "verse_cv_threshold": 0.3,
                    "speaker_ratio_threshold": 0.15,
                    "fragment_ratio_threshold": 0.2,
                },
                "validation": {
                    "min_template_confidence": 0.5,
                    "min_ocr_confidence": 0.3,
                    "min_genre_confidence": 0.5,
                },
                "performance": {
                    "stage1_parallel_workers": 4,
                    "stage2a_parallel_workers": 4,
                    "stage3_batch_size": 1,
                },
            },
            # Memory Management
            "memory": {
                "small_file_threshold_mb": 5,
                "medium_file_threshold_mb": 20,
                "large_file_threshold_mb": 50,
                "memory_check_threshold_mb": 100.0,
            },
            # Formatting/Output Settings
            "formatting": {
                "debug_mode": False,  # Enable debug output in HTML
                "use_simple_formatting": True,  # Use simplified formatting
                "html": {
                    "font_family": "Arial, sans-serif",
                    "metadata_font_size": "12px",
                    "metadata_color": "#666",
                    "body_margin": "20px",
                },
                # Future formatting thresholds (for advanced formatter)
                "thresholds": {
                    "indent_threshold": 0.06,  # 6% indent for fragment references
                    "font_size_ratio_threshold": 0.85,  # Footnote text size ratio
                    "margin_left_threshold": 0.08,  # Left margin detection
                    "margin_right_threshold": 0.92,  # Right margin detection
                },
            },
            # Markdown Converter Settings
            "markdown": {
                "large_file_threshold_mb": 5,
                "chunk_size_mb": 10,
            },
            # Error Handling/Retry Settings
            "error_handling": {
                "max_retries": 3,
                "initial_delay_seconds": 1.0,
                "max_delay_seconds": 60.0,
                "backoff_factor": 2.0,
            },
            # UI/Display Settings
            "ui": {
                "default_window_width": 1000,
                "default_window_height": 800,
                "default_font_size": 14,
                "default_tab": "text",  # text, markdown, html, json
            },
        }


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        ConfigManager: The configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
