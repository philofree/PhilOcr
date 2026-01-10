#!/usr/bin/env python3
"""Chunk and page marker processor for alternative formats.

This module handles processing of chunk and page markers in text content
using regex patterns.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ChunkPageProcessor:
    """Processes chunk and page markers in text using regex patterns."""

    # Regex patterns for parsing chunked formats
    CHUNK_PATTERN = r"--- Chunk (\d+) \(Pages (\d+)-(\d+)\) ---"
    PAGE_PATTERN = r"-{5} Page (\d+) -{5}"
    DOCUMENT_PATTERN = r"---\s+Document\s+(\d+):\s+([^(]+)\s+\((\d+)\s+pages\)\s+---"

    @staticmethod
    def process_chunks(
        text: str,
        markdown_parts: list[str],
        page_content_map: dict[int, str],
        chunk_matches: list[re.Match[str]],
    ) -> None:
        """Process chunk markers in text.

        Args:
            text: Text content containing chunk markers.
            markdown_parts: List to append markdown content to.
            page_content_map: Dictionary mapping page numbers to content.
            chunk_matches: List of regex matches for chunk markers.
        """
        for i, chunk_match in enumerate(chunk_matches):
            chunk_num = chunk_match.group(1)
            start_page = chunk_match.group(2)
            end_page = chunk_match.group(3)

            markdown_parts.append(
                f"### Chunk {chunk_num} (Pages {start_page}-{end_page})"
            )
            markdown_parts.append("")

            # Get chunk boundaries
            chunk_start = chunk_match.end()
            chunk_end = len(text)
            if i < len(chunk_matches) - 1:
                chunk_end = chunk_matches[i + 1].start()

            # Extract chunk content
            chunk_content = text[chunk_start:chunk_end]

            # Process pages within this chunk
            ChunkPageProcessor.process_pages(
                chunk_content, markdown_parts, page_content_map
            )

    @staticmethod
    def process_pages(
        text: str,
        markdown_parts: list[str],
        page_content_map: dict[int, str],
    ) -> None:
        """Process page markers in text.

        Args:
            text: Text content containing page markers.
            markdown_parts: List to append markdown content to.
            page_content_map: Dictionary mapping page numbers to content.
        """
        page_matches = list(re.finditer(ChunkPageProcessor.PAGE_PATTERN, text))

        for j, page_match in enumerate(page_matches):
            page_num = page_match.group(1)
            page_start = page_match.end()
            page_end = len(text)
            if j < len(page_matches) - 1:
                page_end = page_matches[j + 1].start()

            # Get page content
            page_content = text[page_start:page_end].strip()

            # Add page header
            markdown_parts.append(f"#### Page {page_num}")
            markdown_parts.append("")

            # Use detailed content from document_data if available
            try:
                page_num_int = int(page_num)
                if page_num_int in page_content_map:
                    markdown_parts.append(page_content_map[page_num_int])
                    markdown_parts.append("")
                elif page_content:
                    markdown_parts.append(page_content)
                    markdown_parts.append("")
            except (ValueError, KeyError):
                if page_content:
                    markdown_parts.append(page_content)
                    markdown_parts.append("")

    @staticmethod
    def process_implicit_first_chunk(
        text: str,
        chunk_matches: list[re.Match[str]],
        doc_matches: list[re.Match[str]],
        markdown_parts: list[str],
        page_content_map: dict[int, str],
    ) -> None:
        """Process implicit first chunk (between document marker and first chunk).

        Args:
            text: Text content containing markers.
            chunk_matches: List of regex matches for chunk markers.
            doc_matches: List of regex matches for document markers.
            markdown_parts: List to append markdown content to.
            page_content_map: Dictionary mapping page numbers to content.
        """
        try:
            doc_match = doc_matches[0]
            doc_end = doc_match.end()
            chunk_start = chunk_matches[0].start()

            if doc_end >= chunk_start:
                return

            # Extract the implicit first chunk content
            first_chunk_content = text[doc_end:chunk_start]

            # Determine chunk boundaries
            first_chunk_num = "1"
            first_start_page = "1"
            if len(chunk_matches) > 0:
                second_chunk_start_page = int(chunk_matches[0].group(2))
                first_end_page = str(second_chunk_start_page - 1)
            else:
                first_end_page = "15"

            markdown_parts.append(
                f"### Chunk {first_chunk_num} (Pages {first_start_page}-{first_end_page})"
            )
            markdown_parts.append("")

            # Always add Page 1 first
            if 1 in page_content_map:
                markdown_parts.append("#### Page 1")
                markdown_parts.append("")
                markdown_parts.append(page_content_map[1])
                markdown_parts.append("")

            # Process pages within the implicit first chunk
            ChunkPageProcessor.process_pages(
                first_chunk_content, markdown_parts, page_content_map
            )

        except (IndexError, ValueError, AttributeError) as e:
            logger.warning(
                "implicit_first_chunk_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

    @staticmethod
    def process_documents_with_chunks(
        text: str,
        doc_matches: list[re.Match[str]],
        markdown_parts: list[str],
    ) -> str:
        """Process documents with chunk markers.

        Args:
            text: Text content containing document and chunk markers.
            doc_matches: List of regex matches for document markers.
            markdown_parts: List to append markdown content to.

        Returns:
            Complete markdown string.
        """
        try:
            for i, doc_match in enumerate(doc_matches):
                doc_num = doc_match.group(1)
                doc_name = doc_match.group(2).strip()
                doc_pages = doc_match.group(3)

                doc_start = doc_match.end()
                doc_end = len(text)
                if i < len(doc_matches) - 1:
                    doc_end = doc_matches[i + 1].start()

                doc_content = text[doc_start:doc_end]

                markdown_parts.append(f"## Document {doc_num}: {doc_name}")
                markdown_parts.append(f"Total Pages: {doc_pages}")
                markdown_parts.append("")

                chunk_matches = list(
                    re.finditer(ChunkPageProcessor.CHUNK_PATTERN, doc_content)
                )

                if chunk_matches:
                    empty_page_map: dict[int, str] = {}
                    ChunkPageProcessor.process_chunks(
                        doc_content, markdown_parts, empty_page_map, chunk_matches
                    )
                else:
                    # No chunks, just pages
                    page_matches = list(
                        re.finditer(ChunkPageProcessor.PAGE_PATTERN, doc_content)
                    )
                    empty_page_map: dict[int, str] = {}
                    ChunkPageProcessor.process_pages(
                        doc_content, markdown_parts, empty_page_map
                    )

            markdown = "\n".join(markdown_parts)
            return markdown

        except (AttributeError, ValueError, re.error) as e:
            logger.error(
                "documents_with_chunks_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.markdown_converter.exceptions import (
                AlternativeFormatError,
            )

            flush_loggers()
            raise AlternativeFormatError(
                f"Failed to process documents with chunks: {e}"
            ) from e
