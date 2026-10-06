"""Temporary file management for chunk cleanup.

Registers chunk paths with TempFileCleaner; deletion is owned by LifecycleManager.
"""

from __future__ import annotations

from typing import Any

from philocr.utils.logging_config import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """Registers temporary chunk paths for later cleanup."""

    def __init__(self, temp_cleaner: Any) -> None:
        """Initialize temp file manager.

        Args:
            temp_cleaner: TempFileCleaner instance (required)

        Raises:
            ValueError: If temp_cleaner is None
        """
        super().__init__()
        if temp_cleaner is None:
            raise ValueError(
                "temp_cleaner is required; registered-file cleanup is owned by "
                "LifecycleManager on the main thread."
            )
        self.temp_cleaner = temp_cleaner

    def cleanup_chunk_file(self, chunk_path: str, original_file_path: str) -> None:
        """Register a temporary chunk for cleanup on the main thread.

        Args:
            chunk_path: Path to the chunk file
            original_file_path: Path to the original file (to avoid deleting)
        """
        if chunk_path == original_file_path:
            return

        self.temp_cleaner.register_temp_file(chunk_path)
        logger.debug("temp_chunk_registered", file_path=chunk_path)
