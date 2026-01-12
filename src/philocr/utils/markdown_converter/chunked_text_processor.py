#!/usr/bin/env python3
"""Chunked text processor for alternative JSON formats.

This module handles processing of chunked text and simple text formats
that don't have files arrays.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from philocr.utils.logging_config import flush_loggers
from philocr.utils.markdown_converter.chunk_page_processor import ChunkPageProcessor
from philocr.utils.markdown_converter.exceptions import AlternativeFormatError
from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ChunkedTextProcessor:
    """Processes chunked text and simple text formats."""

    @staticmethod
    def process_chunked(
        json_data: dict[str, Any],
        markdown_parts: list[str],
        is_chunked_format: bool,
    ) -> str:
        """Process chunked text format.

        Args:
            json_data: JSON data with text field.
            markdown_parts: List to append markdown content to.
            is_chunked_format: Whether format contains chunk markers.

        Returns:
            Complete markdown string.

        Raises:
            AlternativeFormatError: If processing fails.
        """
        try:
            text = normalize_to_nfc(json_data["text"])

            if not is_chunked_format:
                return ChunkedTextProcessor.process_simple(text, markdown_parts)

            # Look for document markers
            doc_matches = list(re.finditer(ChunkPageProcessor.DOCUMENT_PATTERN, text))

            if doc_matches:
                return ChunkPageProcessor.process_documents_with_chunks(
                    text, doc_matches, markdown_parts
                )
            # No document markers, look for chunks directly
            chunk_matches = list(
                re.finditer(ChunkPageProcessor.CHUNK_PATTERN, text)
            )

            if chunk_matches:
                empty_page_map: dict[int, str] = {}
                ChunkPageProcessor.process_chunks(
                    text, markdown_parts, empty_page_map, chunk_matches
                )
            else:
                return ChunkedTextProcessor.process_simple(text, markdown_parts)

            markdown = "\n".join(markdown_parts)
            logger.info(
                "alternative_format_conversion_completed",
                markdown_length=len(markdown),
            )
            return markdown

        except (KeyError, ValueError, AttributeError, re.error) as e:
            logger.error(
                "chunked_text_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise AlternativeFormatError(f"Failed to process chunked text: {e}") from e

    @staticmethod
    def process_simple(text: str, markdown_parts: list[str]) -> str:
        """Process simple text format without chunks.

        Args:
            text: Text content to process.
            markdown_parts: List to append markdown content to.

        Returns:
            Complete markdown string.

        Raises:
            AlternativeFormatError: If processing fails.
        """
        try:
            lines = text.split("\n")
            in_document = False
            current_document = ""

            for line in lines:
                if line.startswith("--- Document "):
                    if in_document and current_document:
                        markdown_parts.append(current_document)
                        markdown_parts.append("")

                    in_document = True
                    current_document = line
                    markdown_parts.append(f"## {line}")
                    markdown_parts.append("")
                elif line.startswith("----- Page "):
                    page_match: re.Match[str] | None = re.search(
                        r"-{5} Page (\d+) -{5}", line
                    )
                    if page_match:
                        page_num = page_match.group(1)
                        markdown_parts.append(f"### Page {page_num}")
                        markdown_parts.append("")
                elif line.startswith("--- Chunk "):
                    markdown_parts.append(f"#### {line}")
                    markdown_parts.append("")
                elif line.strip():
                    markdown_parts.append(normalize_to_nfc(line.strip()))

            if (
                in_document
                and current_document
                and current_document not in markdown_parts
            ):
                markdown_parts.append(current_document)

            markdown = "\n".join(markdown_parts)
            logger.info(
                "alternative_format_conversion_completed",
                markdown_length=len(markdown),
            )
            return markdown

        except (AttributeError, ValueError) as e:
            logger.error(
                "simple_text_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise AlternativeFormatError(f"Failed to process simple text: {e}") from e
