"""Split document processing for large PDFs.

This module handles processing of PDFs that need to be split into chunks
without UI dependencies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.processing.pdf_utils import split_pdf
from philocr.utils.exceptions import PDFParseError, PDFProcessingError
from philocr.workers.handlers.chunk_processor import ChunkProcessor
from philocr.workers.handlers.layout_combiner import LayoutCombiner

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class SplitDocumentProcessor:
    """Processes documents that need to be split into chunks."""

    def __init__(
        self,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
        on_text_update: Callable[[str], None],
        temp_file_manager: Any,
    ) -> None:
        """Initialize split document processor.

        Args:
            on_status_update: Callback for status updates
            on_progress_update: Callback for progress updates (0-100)
            on_text_update: Callback for text content updates
            temp_file_manager: TempFileManager instance for cleanup
        """
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update
        self.on_text_update = on_text_update
        self.temp_file_manager = temp_file_manager

        # Initialize processors
        self.chunk_processor = ChunkProcessor(
            on_status_update=on_status_update,
            on_progress_update=on_progress_update,
        )
        self.layout_combiner = LayoutCombiner()

    def process_split_document(
        self,
        file_path: str,
        page_count: int,
        max_pages: int,
        file_name: str,
        rate_limiter: Any,
    ) -> tuple[str, dict[str, Any], int]:
        """Process a document that needs to be split into chunks.

        Args:
            file_path: Path to the PDF file
            page_count: Total number of pages
            max_pages: Maximum pages per chunk
            file_name: Name of the file being processed
            rate_limiter: Rate limiter for API calls

        Returns:
            Tuple of (all_text, combined_document_layout, total_chunks)

        Raises:
            ValueError: If splitting fails
            PDFProcessingError: If chunk processing fails
            PDFParseError: If chunk parsing fails
        """
        self.on_status_update(
            f"Document has {page_count} pages. Splitting into chunks..."
        )
        logger.info(
            "document_splitting_required",
            file_name=file_name,
            page_count=page_count,
            max_pages=max_pages,
        )

        pdf_chunks = split_pdf(file_path, max_pages=max_pages)
        logger.debug(
            "pdf_split_completed",
            chunk_count=len(pdf_chunks),
            file_path=file_path,
        )

        if len(pdf_chunks) <= 1 and page_count > max_pages:
            logger.error(
                "pdf_splitting_failed",
                file_path=file_path,
                page_count=page_count,
                max_pages=max_pages,
                chunk_count=len(pdf_chunks),
            )
            raise ValueError(
                "Failed to split the document into smaller chunks. "
                "The document may have security restrictions."
            )

        all_text = ""
        total_chunks = len(pdf_chunks)
        combined_document_layout: dict[str, Any] = {"text": "", "pages": []}

        for i, chunk_path in enumerate(pdf_chunks):
            try:
                base_page_num = i * max_pages
                chunk_text, chunk_layout, chunk_pages = (
                    self.chunk_processor.process_chunk(
                        chunk_path,
                        i,
                        total_chunks,
                        base_page_num,
                        rate_limiter,
                        max_pages,
                    )
                )

                self.layout_combiner.combine_chunk_layouts(
                    chunk_layout, combined_document_layout, base_page_num
                )

                adjusted_text = ChunkProcessor.adjust_page_numbers(
                    chunk_text, chunk_pages, base_page_num, i
                )
                all_text += adjusted_text

            except (PDFProcessingError, PDFParseError) as e:
                logger.error(
                    "chunk_processing_error",
                    chunk_number=i + 1,
                    chunk_path=chunk_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                start_page = i * max_pages + 1
                end_page = min((i + 1) * max_pages, page_count)
                all_text += (
                    f"\n\n--- Error processing pages {start_page} to {end_page} ---\n\n"
                )
                all_text += f"An error occurred while processing this section: {str(e)}"
            except Exception as e:
                # Catch unexpected errors for this chunk but continue processing
                logger.error(
                    "chunk_processing_unexpected_error",
                    chunk_number=i + 1,
                    chunk_path=chunk_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                start_page = i * max_pages + 1
                end_page = min((i + 1) * max_pages, page_count)
                all_text += f"\n\n--- Unexpected error processing pages {start_page} to {end_page} ---\n\n"
                all_text += f"An unexpected error occurred: {str(e)}"

            self.temp_file_manager.cleanup_chunk_file(chunk_path, file_path)

        self.on_text_update(all_text)
        self.on_status_update(
            f"Completed. Processed {page_count} pages in {total_chunks} chunks."
        )

        return all_text, combined_document_layout, total_chunks
