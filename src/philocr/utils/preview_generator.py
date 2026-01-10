"""Preview content generation utilities.

This module provides functions for generating preview content from JSON data
without UI dependencies, allowing for better separation of concerns.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from philocr.utils.document_ai_formatter import extract_text_only
from philocr.utils.json_handler import JSONHandler
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


class PreviewContent:
    """Container for all preview content formats."""

    def __init__(
        self,
        text: str,
        html: str,
        markdown_preview: str,
        full_markdown: str | None,
        json_preview: str,
        markdown_was_truncated: bool = False,
    ) -> None:
        """Initialize preview content.

        Args:
            text: Plain text content
            html: HTML formatted content
            markdown_preview: Truncated markdown for preview
            full_markdown: Full markdown content (may be None if truncated)
            json_preview: Formatted JSON string
            markdown_was_truncated: Whether markdown was truncated
        """
        self.text = text
        self.html = html
        self.markdown_preview = markdown_preview
        self.full_markdown = full_markdown
        self.json_preview = json_preview
        self.markdown_was_truncated = markdown_was_truncated


def generate_all_previews(
    json_data: dict[str, Any], max_preview_length: int = MAX_PREVIEW_LENGTH
) -> PreviewContent:
    """Generate all preview content formats from JSON data.

    Args:
        json_data: The JSON data to convert
        max_preview_length: Maximum length for markdown preview

    Returns:
        PreviewContent object with all preview formats
    """
    if not json_data:
        logger.error("preview_generation_empty_json")
        empty_html = "<html><body><p>No data available</p></body></html>"
        return PreviewContent(
            text="No data available",
            html=empty_html,
            markdown_preview="No data available",
            full_markdown=None,
            json_preview="{}",
        )

    # Generate JSON preview
    json_preview = json.dumps(json_data, indent=2, ensure_ascii=False)

    # Extract text
    text_content = extract_text_only(json_data) or "No text content could be extracted."

    # Generate HTML
    logger.info("html_preview_generation_starting")
    html_content = JSONHandler.convert_to_html(json_data)
    logger.info("html_preview_generation_completed", html_length=len(html_content))

    # Generate Markdown
    logger.info("markdown_preview_generation_starting")
    raw_markdown = JSONHandler.convert_to_markdown(json_data)
    markdown_result = process_markdown_for_preview(raw_markdown, max_preview_length)

    return PreviewContent(
        text=text_content,
        html=html_content,
        markdown_preview=markdown_result.preview_text,
        full_markdown=markdown_result.full_content,
        json_preview=json_preview,
        markdown_was_truncated=markdown_result.was_truncated,
    )


def generate_text_preview(json_data: dict[str, Any]) -> str:
    """Generate text preview from JSON data.

    Args:
        json_data: The JSON data to extract text from

    Returns:
        Extracted text content
    """
    return extract_text_only(json_data) or "No text content could be extracted."


def generate_html_preview(json_data: dict[str, Any]) -> str:
    """Generate HTML preview from JSON data.

    Args:
        json_data: The JSON data to convert

    Returns:
        HTML formatted content
    """
    return JSONHandler.convert_to_html(json_data)


def generate_markdown_preview(
    json_data: dict[str, Any], max_length: int = MAX_PREVIEW_LENGTH
) -> tuple[str, str | None, bool]:
    """Generate markdown preview from JSON data.

    Args:
        json_data: The JSON data to convert
        max_length: Maximum length for preview

    Returns:
        Tuple of (preview_text, full_content, was_truncated)
    """
    raw_markdown = JSONHandler.convert_to_markdown(json_data)
    result = process_markdown_for_preview(raw_markdown, max_length)
    return (result.preview_text, result.full_content, result.was_truncated)
