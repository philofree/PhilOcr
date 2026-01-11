#!/usr/bin/env python3
"""Markdown Debug Service.

This module provides debug functionality for markdown conversion testing,
separating debug logic from UI concerns.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from philocr.utils.markdown_converter.markdown_handler import MarkdownHandler
from philocr.utils.markdown_preview_helper import (
    MAX_PREVIEW_LENGTH,
    process_markdown_for_preview,
)

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class MarkdownDebugResult(NamedTuple):
    """Result of markdown debug test.

    Attributes:
        success: Whether the debug test succeeded
        full_markdown: The full markdown content (None if failed)
        display_content: The content to display in preview (may be truncated)
        error_message: Error message if failed, None otherwise
    """

    success: bool
    full_markdown: str | None
    display_content: str
    error_message: str | None


class MarkdownDebugService:
    """Service for running markdown debug tests."""

    CONTENT_SEPARATOR = "Content:\n\n"

    @classmethod
    def run_debug_test(
        cls, max_preview_length: int = MAX_PREVIEW_LENGTH
    ) -> MarkdownDebugResult:
        """Run a debug test of markdown conversion.

        Args:
            max_preview_length: Maximum length for preview display

        Returns:
            MarkdownDebugResult with test results and formatted content
        """
        logger.info("debug_markdown_test_starting")
        try:
            debug_result_raw = MarkdownHandler.debug_markdown_conversion()
            return cls.format_debug_result(debug_result_raw, max_preview_length)
        except Exception as e:
            logger.error(
                "debug_markdown_test_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Markdown debug test failed - {e}") from e

    @classmethod
    def format_debug_result(
        cls,
        debug_result_raw: str,
        max_preview_length: int = MAX_PREVIEW_LENGTH,
    ) -> MarkdownDebugResult:
        """Format debug result for display.

        Args:
            debug_result_raw: Raw debug result from MarkdownHandler
            max_preview_length: Maximum length for preview display

        Returns:
            MarkdownDebugResult with formatted content
        """
        if cls.CONTENT_SEPARATOR not in debug_result_raw:
            return MarkdownDebugResult(
                success=True,
                full_markdown=None,
                display_content=debug_result_raw,
                error_message=None,
            )

        # Extract markdown content
        parts = debug_result_raw.split(cls.CONTENT_SEPARATOR, 1)
        header = parts[0]
        full_markdown = parts[1] if len(parts) > 1 else None

        if not full_markdown:
            return MarkdownDebugResult(
                success=True,
                full_markdown=None,
                display_content=debug_result_raw,
                error_message=None,
            )

        # Process markdown for preview (includes truncation if needed)
        preview_result = process_markdown_for_preview(full_markdown, max_preview_length)

        # Combine header with preview content
        if preview_result.was_truncated:
            display_content = (
                f"{header}{cls.CONTENT_SEPARATOR}{preview_result.preview_text}"
            )
        else:
            display_content = debug_result_raw

        return MarkdownDebugResult(
            success=True,
            full_markdown=preview_result.full_content,
            display_content=display_content,
            error_message=None,
        )
