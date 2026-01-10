"""Batch file processing handler.

This module handles processing logic for batch PDF files without UI dependencies.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.processing.document_ai import process_pdf
from philocr.processing.pdf_utils import get_pdf_page_count
from philocr.utils.exceptions import PDFProcessingError
from philocr.utils.logging_config import flush_loggers
from philocr.workers.handlers.chunk_processor import ChunkProcessor
from philocr.workers.handlers.layout_combiner import LayoutCombiner
from philocr.workers.handlers.temp_file_manager import TempFileManager

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class BatchFileHandler:
    """Handles batch file processing operations."""

    def __init__(
        self,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
        temp_file_manager: Any | None = None,
    ) -> None:
        """Initialize batch file handler.

        Args:
            on_status_update: Callback for status updates
            on_progress_update: Callback for progress updates (0-100)
            temp_file_manager: Optional TempFileManager instance
        """
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update
        self.temp_file_manager = temp_file_manager or TempFileManager()

    def count_total_chunks(self, batch_files: list[str], max_pages: int = 15) -> int:
        """Count total chunks needed for all batch files.

        Args:
            batch_files: List of file paths to process
            max_pages: Maximum pages per chunk

        Returns:
            Total number of chunks expected
        """
        total_chunks = 0
        for file_path in batch_files:
            try:
                page_count = get_pdf_page_count(file_path)
                if page_count > max_pages:
                    num_chunks = (page_count + max_pages - 1) // max_pages
                    total_chunks += num_chunks
                else:
                    total_chunks += 1
            except Exception as e:
                logger.error(
                    "batch_page_count_error",
                    file_path=file_path,
                    file_name=file_path.split("/")[-1],
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                # Assume at least 1 chunk even if we can't determine page count
                total_chunks += 1
        return total_chunks

    def process_single_file_in_batch(
        self,
        file_path: str,
        file_index: int,
        total_files: int,
        rate_limiter: Any,
        processed_chunks: int,
        total_chunks: int,
        max_pages: int = 15,
    ) -> tuple[str, dict[str, Any] | None, int]:
        """Process a single file in batch mode (no splitting needed).

        Args:
            file_path: Path to the file
            file_index: Index of file in batch (0-based)
            total_files: Total number of files
            rate_limiter: Rate limiter for API calls
            processed_chunks: Current processed chunks count
            total_chunks: Total chunks expected
            max_pages: Maximum pages per chunk

        Returns:
            Tuple of (file_text, document_layout, new_processed_chunks)
        """
        overall_progress = int((processed_chunks / total_chunks) * 100)
        new_processed_chunks = processed_chunks + 1
        self.on_progress_update(overall_progress)

        file_name = file_path.split("/")[-1]
        try:
            file_text, document_layout = process_pdf(file_path, rate_limiter)
        except Exception as e:
            logger.error(
                "batch_file_processing_error",
                file_index=file_index + 1,
                file_name=file_name,
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            error_msg = f"Error processing {file_name}: {str(e)}"
            flush_loggers()
            raise PDFProcessingError(file_path, error_msg) from e

        return file_text, document_layout, new_processed_chunks

    def process_split_file_in_batch(
        self,
        file_path: str,
        file_index: int,
        total_files: int,
        page_count: int,
        max_pages: int,
        rate_limiter: Any,
        processed_chunks: int,
        total_chunks: int,
    ) -> tuple[str, dict[str, Any] | None, int]:
        """Process a file that needs splitting in batch mode.

        Args:
            file_path: Path to the file
            file_index: Index of file in batch (0-based)
            total_files: Total number of files
            page_count: Number of pages in file
            max_pages: Maximum pages per chunk
            rate_limiter: Rate limiter for API calls
            processed_chunks: Current processed chunks count
            total_chunks: Total chunks expected

        Returns:
            Tuple of (file_text, document_layout, new_processed_chunks)
        """
        from philocr.processing.pdf_utils import split_pdf

        self.on_status_update(
            f"Document has {page_count} pages. Splitting into chunks..."
        )

        pdf_chunks = split_pdf(file_path, max_pages=max_pages)
        total_file_chunks = len(pdf_chunks)
        file_name = os.path.basename(file_path)
        logger.debug(
            "file_split_into_chunks",
            file_name=file_name,
            file_path=file_path,
            chunk_count=total_file_chunks,
            page_count=page_count,
        )

        file_text = ""
        combined_document_layout: dict[str, Any] = {"text": "", "pages": []}
        new_processed_chunks = processed_chunks

        # Create batch-aware progress updater
        def batch_progress_updater(chunk_progress: int) -> None:
            """Update progress within chunk processing."""
            overall_progress = int((new_processed_chunks / total_chunks) * 100)
            self.on_progress_update(overall_progress)

        chunk_processor = ChunkProcessor(
            on_status_update=self._batch_status_updater(
                file_index, total_files, file_name, total_file_chunks
            ),
            on_progress_update=batch_progress_updater,
        )
        layout_combiner = LayoutCombiner()

        for j, chunk_path in enumerate(pdf_chunks):
            overall_progress = int((new_processed_chunks / total_chunks) * 100)
            new_processed_chunks += 1

            try:
                base_page_num = j * max_pages
                chunk_text, chunk_layout, chunk_pages = chunk_processor.process_chunk(
                    chunk_path,
                    j,
                    total_file_chunks,
                    base_page_num,
                    rate_limiter,
                    max_pages,
                )

                layout_combiner.combine_chunk_layouts(
                    chunk_layout, combined_document_layout, base_page_num
                )

                adjusted_text = ChunkProcessor.adjust_page_numbers(
                    chunk_text, chunk_pages, base_page_num, j
                )
                file_text += adjusted_text

            except (PDFProcessingError, Exception) as e:
                logger.error(
                    "batch_chunk_processing_error",
                    file_index=file_index + 1,
                    file_name=file_name,
                    chunk_number=j + 1,
                    chunk_path=chunk_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                file_text += f"\n\n--- Error in chunk {j+1} ---\n\n"
                file_text += f"An error occurred processing this section: {str(e)}"

            self.temp_file_manager.cleanup_chunk_file(chunk_path, file_path)

        return file_text, combined_document_layout, new_processed_chunks

    def _batch_status_updater(
        self, file_index: int, total_files: int, file_name: str, total_chunks: int
    ) -> Callable[[str], None]:
        """Create a status updater that includes batch file info."""

        def update_status(status: str) -> None:
            """Update status with batch file context."""
            chunk_msg = (
                f"Processing {file_index+1}/{total_files}: " f"{file_name} - {status}"
            )
            self.on_status_update(chunk_msg)

        return update_status

    @staticmethod
    def handle_file_error(
        file_index: int,
        file_name: str,
        page_count: int,
        max_pages: int,
        error: Exception,
        processed_chunks: int,
        total_chunks: int,
        on_progress_update: Callable[[int], None],
    ) -> tuple[str, int]:
        """Handle error processing a file in batch mode.

        Args:
            file_index: Index of file in batch (0-based)
            file_name: Name of the file
            page_count: Page count of the file
            max_pages: Maximum pages per chunk
            error: Exception that occurred
            processed_chunks: Current processed chunks count
            total_chunks: Total chunks expected
            on_progress_update: Callback to update progress

        Returns:
            Tuple of (error_text, new_processed_chunks)
        """
        error_text = (
            f"\n\n--- Error processing document {file_index+1}: " f"{file_name} ---\n"
        )
        error_text += f"An error occurred: {str(error)}\n"

        if page_count > max_pages:
            estimated_chunks = (page_count + max_pages - 1) // max_pages
        else:
            estimated_chunks = 1

        new_processed_chunks = processed_chunks + estimated_chunks
        current_progress = int((new_processed_chunks / total_chunks) * 100)
        on_progress_update(current_progress)

        return error_text, new_processed_chunks
