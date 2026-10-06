#!/usr/bin/env python3
"""Lifecycle Manager for MainWindow.

This module handles cleanup and lifecycle events including
temp file cleanup and window close operations.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    import structlog
    from PyQt6.QtGui import QCloseEvent

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class LifecycleManager:
    """Manages lifecycle and cleanup operations for MainWindow.

    Handles temp file cleanup and window close events to improve
    cohesion and maintainability in MainWindow.
    """

    def __init__(
        self,
        temp_cleaner: Any,  # TempFileCleaner
        on_status_update: Callable[[str], None],
    ) -> None:
        """Initialize the Lifecycle Manager.

        Args:
            temp_cleaner: Temporary file cleaner instance
            on_status_update: Callback for status updates
        """
        super().__init__()
        self.temp_cleaner = temp_cleaner
        self.on_status_update = on_status_update

    def cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        if not self.temp_cleaner:
            return

        cleaned, _failed = self.temp_cleaner.clean_registered_files()
        if cleaned > 0:
            self.on_status_update(f"Cleaned {cleaned} temporary files")

    def on_window_close(self, event: QCloseEvent) -> None:
        """Handle window close event and clean up resources.

        Args:
            event: Close event
        """
        self.cleanup_temp_files()
        event.accept()
