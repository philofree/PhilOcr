"""Chunk processing utilities for split PDF documents.

This module handles processing of individual PDF chunks and page number
adjustments without UI dependencies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.processing.document_ai import process_pdf
from philocr.processing.pdf_utils import get_pdf_page_count

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ChunkProcessor:
    """Processes individual PDF chunks and adjusts page numbers."""

    def __init__(
        self,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
    ) -> None:
        """Initialize chunk processor.

        Args:
            on_status_update: Callback for status updates
            on_progress_update: Callback for progress updates (0-100)
        """
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update

    def process_chunk(
        self,
        chunk_path: str,
        chunk_index: int,
        total_chunks: int,
        base_page_num: int,
        rate_limiter: Any,
        max_pages: int,
    ) -> tuple[str, dict[str, Any], int]:
        """Process a single chunk of a split PDF.

        Args:
            chunk_path: Path to the chunk file
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks
            base_page_num: Base page number for this chunk
            rate_limiter: Rate limiter for API calls
            max_pages: Maximum pages per chunk

        Returns:
            Tuple of (chunk_text, chunk_layout, chunk_pages)

        Raises:
            ValueError: If chunk exceeds max_pages limit
        """
        chunk_status = f"Processing chunk {chunk_index+1} of {total_chunks}"
        self.on_status_update(chunk_status)
        logger.debug(
            "chunk_processing_started",
            chunk_number=chunk_index + 1,
            total_chunks=total_chunks,
            chunk_path=chunk_path,
        )

        progress_percent = int((chunk_index / total_chunks) * 100)
        self.on_progress_update(progress_percent)

        chunk_pages = get_pdf_page_count(chunk_path)

        if chunk_pages > max_pages:
            logger.error(
                "chunk_exceeds_page_limit",
                chunk_number=chunk_index + 1,
                chunk_pages=chunk_pages,
                max_pages=max_pages,
                chunk_path=chunk_path,
            )
            raise ValueError(
                f"Split PDF chunk still exceeds {max_pages} pages ({chunk_pages})"
            )

        logger.debug(
            "chunk_sending_to_document_ai",
            chunk_number=chunk_index + 1,
            chunk_path=chunk_path,
        )
        chunk_text, chunk_layout = process_pdf(
            chunk_path, rate_limiter, max_pages=max_pages
        )

        return chunk_text, chunk_layout, chunk_pages

    @staticmethod
    def adjust_page_numbers(
        chunk_text: str,
        chunk_pages: int,
        base_page_num: int,
        chunk_index: int,
    ) -> str:
        """Adjust page numbers in chunk text to reflect original document.

        Args:
            chunk_text: Original chunk text with page markers
            chunk_pages: Number of pages in this chunk
            base_page_num: Base page number for this chunk
            chunk_index: Index of this chunk (0-based)

        Returns:
            Text with adjusted page numbers
        """
        if chunk_index > 0:
            chunk_text = (
                f"\n\n--- Chunk {chunk_index+1} "
                f"(Pages {base_page_num + 1}-{base_page_num + chunk_pages}) ---\n\n"
                + chunk_text
            )

        modified_text = chunk_text
        for p in range(2, chunk_pages + 1):
            original_marker = f"----- Page {p} -----"
            new_marker = f"----- Page {base_page_num + p} -----"
            modified_text = modified_text.replace(original_marker, new_marker)

        if chunk_index > 0:
            modified_text = f"----- Page {base_page_num + 1} -----\n\n" + modified_text

        return modified_text
