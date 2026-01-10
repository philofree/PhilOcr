#!/usr/bin/env python3
"""Temporary file cleaner for managing temporary files during processing."""
from __future__ import annotations

import datetime
import glob
import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class TempFileCleaner:
    """Class to manage temporary files created during document processing."""

    def __init__(self, temp_dir: str | None = None) -> None:
        """
        Initialize the temp file cleaner.

        Args:
            temp_dir (Optional[str]): Directory to store temporary files.
                If None, system temp directory will be used.
        """
        super().__init__()
        self.temp_dir: str = temp_dir or tempfile.gettempdir()
        self.temp_files: list[str] = []
        logger.info("temp_cleaner_initialized", temp_dir=self.temp_dir)

    def register_temp_file(self, file_path: str) -> None:
        """
        Register a temporary file for later cleanup.

        Args:
            file_path (str): Path to the temporary file
        """
        if os.path.exists(file_path):
            self.temp_files.append(file_path)
            logger.debug("temp_file_registered", file_path=file_path)

    def register_temp_files(self, file_paths: list[str]) -> None:
        """
        Register multiple temporary files for later cleanup.

        Args:
            file_paths (List[str]): List of paths to temporary files
        """
        for file_path in file_paths:
            self.register_temp_file(file_path)

    def clean_registered_files(self) -> tuple[int, int]:
        """Clean all registered temporary files."""
        cleaned_count: int = 0
        failed_count: int = 0

        for file_path in self.temp_files[:]:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug("temp_file_cleaned", file_path=file_path)
                    cleaned_count += 1
                self.temp_files.remove(file_path)
            except Exception as e:
                logger.error(
                    "temp_file_clean_failed",
                    file_path=file_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                failed_count += 1

        logger.info(
            "temp_files_cleaned_summary",
            cleaned_count=cleaned_count,
            failed_count=failed_count,
        )
        return cleaned_count, failed_count

    def clean_old_temp_files(self, age_hours: int = 24) -> tuple[int, int]:
        """
        Clean temporary files older than the specified age.

        Args:
            age_hours (int): Age in hours to consider files old

        Returns:
            Tuple[int, int]: (number of files cleaned, number of files that failed to clean)
        """
        pattern: str = os.path.join(self.temp_dir, "tmp*pdf")
        now: datetime.datetime = datetime.datetime.now()
        cleaned_count: int = 0
        failed_count: int = 0

        for file_path in glob.glob(pattern):
            try:
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                age = now - file_time

                if age.total_seconds() > age_hours * 3600:
                    os.unlink(file_path)
                    logger.debug(
                        "old_temp_file_cleaned",
                        file_path=file_path,
                        age_hours=age_hours,
                    )
                    cleaned_count += 1
            except Exception as e:
                logger.error(
                    "old_temp_file_clean_failed",
                    file_path=file_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                failed_count += 1

        logger.info(
            "old_temp_files_cleaned_summary",
            cleaned_count=cleaned_count,
            failed_count=failed_count,
            age_hours=age_hours,
        )
        return cleaned_count, failed_count
