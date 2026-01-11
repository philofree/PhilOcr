"""Temporary file management for chunk cleanup.

This module coordinates temporary file cleanup for PDF chunks
without UI dependencies.
"""

from __future__ import annotations

import os
from typing import Any

from philocr.utils.logging_config import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """Manages temporary file cleanup for PDF chunks."""

    def __init__(self, temp_cleaner: Any | None = None) -> None:
        """Initialize temp file manager.

        Args:
            temp_cleaner: Optional TempFileCleaner instance
        """
        self.temp_cleaner = temp_cleaner

    def cleanup_chunk_file(self, chunk_path: str, original_file_path: str) -> None:
        """Clean up a temporary chunk file.

        Args:
            chunk_path: Path to the chunk file
            original_file_path: Path to the original file (to avoid deleting)
        """
        if chunk_path == original_file_path:
            return

        if self.temp_cleaner:
            self.temp_cleaner.register_temp_file(chunk_path)
        else:
            try:
                os.unlink(chunk_path)
                logger.debug("temp_file_deleted", file_path=chunk_path)
            except Exception as e:
                # Even cleanup failures should be logged and fail fast per zero tolerance
                from philocr.utils.logging_config import get_logger

                log = get_logger(__name__)
                log.error(
                    "temp_file_delete_failed",
                    file_path=chunk_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Temp file cleanup failed for {chunk_path} - {e}"
                ) from e
