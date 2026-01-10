#!/usr/bin/env python3
"""File Saver Utilities.

This module provides file saving functionality, separating file I/O
operations from UI concerns.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from philocr.utils.json_handler import JSONHandler

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class MarkdownFileSaver:
    """Handles markdown file save operations."""

    @staticmethod
    def save_markdown_content(
        file_path: str,
        full_markdown: str | None,
        fallback_json: dict[str, Any] | None = None,
    ) -> bool:
        """Save markdown content to a file.

        Args:
            file_path: Path where to save the file
            full_markdown: Full markdown content to save, or None
            fallback_json: JSON data to use if full_markdown is None

        Returns:
            True if successful, False otherwise
        """
        if full_markdown:
            try:
                logger.info(
                    "markdown_file_saving",
                    file_path=file_path,
                    content_length=len(full_markdown),
                    source="stored_content",
                )
                with open(file_path, "w", encoding="utf-8") as md_file:
                    _ = md_file.write(full_markdown)
                logger.info("markdown_file_saved", file_path=file_path)
                return True
            except Exception as e:
                logger.error(
                    "markdown_file_save_exception",
                    file_path=file_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                return False

        if fallback_json:
            logger.info(
                "markdown_file_saving",
                file_path=file_path,
                source="json_handler",
            )
            success = JSONHandler.save_as_markdown(fallback_json, file_path)
            if not success:
                logger.error("markdown_file_save_failed", file_path=file_path)
            return success

        logger.error("markdown_file_save_failed_no_content", file_path=file_path)
        return False
