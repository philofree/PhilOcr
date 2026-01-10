#!/usr/bin/env python3
"""Markdown Preview Helper Utilities.

This module provides helper functions for markdown preview processing,
including truncation and content validation logic.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


# Default preview length limit
MAX_PREVIEW_LENGTH = 50000


class MarkdownPreviewResult(NamedTuple):
    """Result of markdown preview processing.

    Attributes:
        preview_text: The text to display in the preview
        full_content: The full markdown content (for saving)
        was_truncated: Whether the content was truncated for preview
    """

    preview_text: str
    full_content: str | None
    was_truncated: bool


def validate_markdown_content(
    content: str | None,
) -> tuple[bool, str]:
    """Validate markdown content.

    Args:
        content: The markdown content to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    if content is None:
        return False, "Markdown conversion returned None"
    if content.strip() == "":
        return False, "Markdown conversion returned empty content"
    return True, ""


def truncate_markdown_preview(
    full_content: str,
    max_length: int = MAX_PREVIEW_LENGTH,
) -> MarkdownPreviewResult:
    """Truncate markdown content for preview display.

    Args:
        full_content: The full markdown content
        max_length: Maximum length for preview (default: 50000)

    Returns:
        MarkdownPreviewResult with preview text and metadata
    """
    if not full_content:
        return MarkdownPreviewResult(
            preview_text="Error: Markdown conversion failed to produce content.",
            full_content=None,
            was_truncated=False,
        )

    markdown_length = len(full_content)

    # Log preview preview (first 100 chars)
    preview_preview = full_content[:100].replace("\n", "\\n")
    logger.info(
        "markdown_preview_preview",
        preview_preview=preview_preview,
        total_length=markdown_length,
    )

    if markdown_length > max_length:
        truncated_content = full_content[:max_length]
        truncated_content += (
            f"\n\n...\n\n[PREVIEW TRUNCATED: "
            f"Showing {max_length:,} of {markdown_length:,} characters]\n"
        )
        truncated_content += (
            "[The complete content will be saved when using 'Save Markdown']"
        )

        logger.info(
            "markdown_preview_truncated",
            preview_length=max_length,
            total_length=markdown_length,
        )

        return MarkdownPreviewResult(
            preview_text=truncated_content,
            full_content=full_content,
            was_truncated=True,
        )

    return MarkdownPreviewResult(
        preview_text=full_content,
        full_content=full_content,
        was_truncated=False,
    )


def process_markdown_for_preview(
    markdown_content: str | None,
    max_length: int = MAX_PREVIEW_LENGTH,
) -> MarkdownPreviewResult:
    """Process markdown content for preview display.

    This function validates and truncates markdown content as needed.

    Args:
        markdown_content: The markdown content to process
        max_length: Maximum length for preview (default: 50000)

    Returns:
        MarkdownPreviewResult with preview text and metadata
    """
    is_valid, error_msg = validate_markdown_content(markdown_content)
    if not is_valid:
        logger.error(
            "markdown_conversion_returned_empty"
            if markdown_content is None
            else "markdown_conversion_returned_empty"
        )
        return MarkdownPreviewResult(
            preview_text=f"Error: {error_msg}.",
            full_content=None,
            was_truncated=False,
        )

    assert markdown_content is not None  # Type narrowing
    return truncate_markdown_preview(markdown_content, max_length)
