#!/usr/bin/env python3
"""Hybrid format processor for alternative JSON formats.

This module handles processing of hybrid formats that combine chunk markers
in text with document_data structures.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from philocr.utils.logging_config import flush_loggers
from philocr.utils.markdown_converter.alternative_metadata_extractor import (
    AlternativeMetadataExtractor,
)
from philocr.utils.markdown_converter.chunk_page_processor import ChunkPageProcessor
from philocr.utils.markdown_converter.exceptions import AlternativeFormatError
from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class HybridFormatProcessor:
    """Processes hybrid format (chunk markers + document_data)."""

    @staticmethod
    def process(
        json_data: dict[str, Any],
        markdown_parts: list[str],
        page_content_map: dict[int, str],
    ) -> str:
        """Process hybrid format (chunk markers + document_data).

        Args:
            json_data: JSON data in hybrid format.
            markdown_parts: List to append markdown content to.
            page_content_map: Dictionary mapping page numbers to content.

        Returns:
            Complete markdown string.

        Raises:
            AlternativeFormatError: If processing fails.
        """
        logger.info(
            "hybrid_format_detected",
            description="chunk_markers_in_text_and_content_in_document_data",
        )

        try:
            for file_idx, file_data in enumerate(json_data["files"]):
                if not isinstance(file_data, dict):
                    continue

                # Add file metadata
                AlternativeMetadataExtractor.add_file_metadata(
                    file_data, file_idx, markdown_parts
                )

                # Extract detailed content from document_data
                AlternativeMetadataExtractor.extract_page_content(
                    file_data, page_content_map
                )

                # Process text field with chunk and page markers
                if "text" not in file_data:
                    markdown_parts.append("---")
                    markdown_parts.append("")
                    continue

                text = normalize_to_nfc(file_data["text"])
                chunk_matches = list(
                    re.finditer(ChunkPageProcessor.CHUNK_PATTERN, text)
                )
                doc_matches = list(
                    re.finditer(ChunkPageProcessor.DOCUMENT_PATTERN, text)
                )

                # Handle implicit first chunk
                if chunk_matches and chunk_matches[0].group(1) == "2":
                    logger.info("implicit_first_chunk_processing")
                    first_chunk_start = 0
                    first_chunk_end = chunk_matches[0].start()
                    first_chunk_content = normalize_to_nfc(
                        text[first_chunk_start:first_chunk_end]
                    )

                    markdown_parts.append("### Chunk 1 (Pages 1-15)")
                    markdown_parts.append("")

                    if 1 in page_content_map:
                        markdown_parts.append("#### Page 1")
                        markdown_parts.append("")
                        markdown_parts.append(page_content_map[1])
                        markdown_parts.append("")

                    ChunkPageProcessor.process_pages(
                        first_chunk_content, markdown_parts, page_content_map
                    )

                # Process implicit first chunk from document marker
                if doc_matches and chunk_matches:
                    ChunkPageProcessor.process_implicit_first_chunk(
                        text,
                        chunk_matches,
                        doc_matches,
                        markdown_parts,
                        page_content_map,
                    )

                # Process explicit chunks
                ChunkPageProcessor.process_chunks(
                    text, markdown_parts, page_content_map, chunk_matches
                )

                # Add separator between files
                markdown_parts.append("---")
                markdown_parts.append("")

            markdown = "\n".join(markdown_parts)
            logger.info(
                "alternative_format_conversion_completed",
                markdown_length=len(markdown),
            )
            return markdown

        except (KeyError, ValueError, AttributeError, re.error) as e:
            logger.error(
                "hybrid_format_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise AlternativeFormatError(f"Failed to process hybrid format: {e}") from e
