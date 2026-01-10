#!/usr/bin/env python3
"""Metadata extractor for alternative JSON formats.

This module handles extraction and formatting of document, file, and page
metadata from alternative JSON structures.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class AlternativeMetadataExtractor:
    """Extracts and adds metadata from JSON data."""

    @staticmethod
    def add_document_metadata(
        json_data: dict[str, Any], markdown_parts: list[str]
    ) -> None:
        """Add document metadata to markdown parts.

        Args:
            json_data: JSON data containing metadata.
            markdown_parts: List to append markdown content to.
        """
        try:
            if "metadata" in json_data and "mode" in json_data["metadata"]:
                mode = json_data["metadata"]["mode"]
                markdown_parts.append(f"# Document Processing Mode: {mode}")
                markdown_parts.append("")
        except (KeyError, TypeError) as e:
            logger.warning(
                "metadata_extraction_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

    @staticmethod
    def add_file_metadata(
        file_data: dict[str, Any],
        file_idx: int,
        markdown_parts: list[str],
    ) -> None:
        """Add file metadata to markdown parts.

        Args:
            file_data: File data dictionary containing metadata.
            file_idx: Index of the file (0-based).
            markdown_parts: List to append markdown content to.
        """
        try:
            if "metadata" in file_data and "filename" in file_data["metadata"]:
                filename = file_data["metadata"]["filename"]
                page_count = file_data["metadata"].get("page_count", "Unknown")
                markdown_parts.append(f"## File: {filename}")
                markdown_parts.append(f"Total Pages: {page_count}")
                markdown_parts.append("")
            else:
                markdown_parts.append(f"## File {file_idx + 1}")
                markdown_parts.append("")
        except (KeyError, TypeError) as e:
            logger.warning(
                "file_metadata_extraction_failed",
                file_idx=file_idx,
                error=str(e),
                error_type=type(e).__name__,
            )
            markdown_parts.append(f"## File {file_idx + 1}")
            markdown_parts.append("")

    @staticmethod
    def extract_page_content(
        file_data: dict[str, Any], page_content_map: dict[int, str]
    ) -> None:
        """Extract page content from document_data.

        Args:
            file_data: File data dictionary containing document_data.
            page_content_map: Dictionary to populate with page number -> content.
        """
        try:
            if "document_data" in file_data and "pages" in file_data["document_data"]:
                doc_pages = file_data["document_data"]["pages"]
                for page in doc_pages:
                    if "page_number" not in page:
                        continue

                    page_num = page["page_number"]
                    page_texts: list[str] = []

                    # Try to get content from blocks
                    if "blocks" in page:
                        for block in page["blocks"]:
                            if "text" in block and block["text"].strip():
                                page_texts.append(block["text"])

                    # If no blocks, try paragraphs
                    elif "paragraphs" in page:
                        for para in page["paragraphs"]:
                            if "text" in para and para["text"].strip():
                                page_texts.append(para["text"])

                    # Store the combined content for this page
                    if page_texts:
                        page_content_map[page_num] = "\n\n".join(page_texts)

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(
                "page_content_extraction_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
