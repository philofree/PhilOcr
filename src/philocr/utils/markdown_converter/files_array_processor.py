#!/usr/bin/env python3
"""Files array processor for alternative JSON formats.

This module handles processing of files array formats where multiple files
are processed in sequence.
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


class FilesArrayProcessor:
    """Processes files array format."""

    @staticmethod
    def process(
        json_data: dict[str, Any],
        markdown_parts: list[str],
        is_chunked_format: bool,
        page_content_map: dict[int, str],
    ) -> str:
        """Process files array format.

        Args:
            json_data: JSON data with files array.
            markdown_parts: List to append markdown content to.
            is_chunked_format: Whether format contains chunk markers.
            page_content_map: Dictionary mapping page numbers to content.

        Returns:
            Complete markdown string.

        Raises:
            AlternativeFormatError: If processing fails.
        """
        try:
            for file_idx, file_data in enumerate(json_data["files"]):
                AlternativeMetadataExtractor.add_file_metadata(
                    file_data, file_idx, markdown_parts
                )

                if "text" not in file_data:
                    markdown_parts.append("---")
                    markdown_parts.append("")
                    continue

                text = normalize_to_nfc(file_data["text"])
                is_file_chunked = "--- Chunk " in text

                if is_file_chunked:
                    chunk_matches = list(
                        re.finditer(ChunkPageProcessor.CHUNK_PATTERN, text)
                    )
                    doc_matches = list(
                        re.finditer(ChunkPageProcessor.DOCUMENT_PATTERN, text)
                    )

                    if doc_matches and chunk_matches:
                        ChunkPageProcessor.process_implicit_first_chunk(
                            text,
                            chunk_matches,
                            doc_matches,
                            markdown_parts,
                            page_content_map,
                        )

                    ChunkPageProcessor.process_chunks(
                        text, markdown_parts, page_content_map, chunk_matches
                    )
                else:
                    # Standard page marker processing
                    page_matches = list(
                        re.finditer(ChunkPageProcessor.PAGE_PATTERN, text)
                    )

                    for i, match in enumerate(page_matches):
                        page_num = match.group(1)
                        page_start = match.end()
                        page_end = len(text)
                        if i < len(page_matches) - 1:
                            page_end = page_matches[i + 1].start()

                        page_content = normalize_to_nfc(
                            text[page_start:page_end].strip()
                        )

                        markdown_parts.append(f"### Page {page_num}")
                        markdown_parts.append("")
                        if page_content:
                            markdown_parts.append(page_content)
                            markdown_parts.append("")

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
                "files_array_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise AlternativeFormatError(f"Failed to process files array: {e}") from e
