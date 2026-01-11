"""Single file processing handler.

This module handles processing logic for single PDF files without UI dependencies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.processing.document_ai import process_pdf
from philocr.processing.pdf_utils import get_pdf_page_count
from philocr.utils.exceptions import (
    PDFPageCountError,
    PDFParseError,
    PDFProcessingError,
)
from philocr.utils.logging_config import flush_loggers
from philocr.workers.handlers.split_document_processor import SplitDocumentProcessor
from philocr.workers.handlers.temp_file_manager import TempFileManager

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class SingleFileHandler:
    """Handles single file processing operations."""

    def __init__(
        self,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
        on_text_update: Callable[[str], None],
        temp_file_manager: Any | None = None,
    ) -> None:
        """Initialize single file handler.

        Args:
            on_status_update: Callback for status updates
            on_progress_update: Callback for progress updates (0-100)
            on_text_update: Callback for text content updates
            temp_file_manager: TempFileManager instance (required)

        Raises:
            ValueError: If temp_file_manager is None
        """
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update
        self.on_text_update = on_text_update
        if temp_file_manager is None:
            raise ValueError(
                "temp_file_manager is required. "
                "TempFileManager must be provided explicitly."
            )
        self.temp_file_manager = temp_file_manager

    def get_page_count(self, file_path: str) -> int:
        """Get page count for a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Number of pages in the PDF

        Raises:
            PDFPageCountError: If page count cannot be determined
            PDFParseError: If PDF cannot be parsed
        """
        try:
            page_count = get_pdf_page_count(file_path)
            logger.debug(
                "document_page_count_obtained",
                page_count=page_count,
                file_path=file_path,
            )
            return page_count
        except ValueError as e:
            logger.error(
                "pdf_page_count_error",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise PDFParseError(
                file_path,
                "Could not open the PDF file. It may be corrupted or password-protected.",
            ) from e
        except Exception as e:
            logger.error(
                "pdf_page_count_unexpected_error",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise PDFPageCountError(file_path, str(e)) from e

    def process_document(
        self,
        file_path: str,
        file_name: str,
        rate_limiter: Any,
        max_pages: int = 15,
    ) -> tuple[str, dict[str, Any] | None]:
        """Process a single document that doesn't need splitting.

        Args:
            file_path: Path to the PDF file
            file_name: Name of the file
            rate_limiter: Rate limiter for API calls
            max_pages: Maximum pages limit (default: 15)

        Returns:
            Tuple of (extracted_text, document_layout)

        Raises:
            PDFProcessingError: If processing fails
        """
        self.on_status_update(f"Processing document normally (under {max_pages} pages)")
        logger.debug(
            "document_processing_normally",
            file_path=file_path,
            file_name=file_name,
            max_pages=max_pages,
        )

        self.on_progress_update(50)

        try:
            extracted_text, document_layout = process_pdf(
                file_path, rate_limiter, max_pages=max_pages
            )
        except Exception as e:
            logger.error(
                "document_processing_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise PDFProcessingError(file_path, str(e)) from e

        return extracted_text, document_layout

    def should_split(self, page_count: int, max_pages: int) -> bool:
        """Determine if a document needs to be split.

        Args:
            page_count: Number of pages in the document
            max_pages: Maximum pages per chunk

        Returns:
            True if document should be split, False otherwise
        """
        return page_count > max_pages

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
        split_processor = SplitDocumentProcessor(
            on_status_update=self.on_status_update,
            on_progress_update=self.on_progress_update,
            on_text_update=self.on_text_update,
            temp_file_manager=self.temp_file_manager,
        )
        return split_processor.process_split_document(
            file_path, page_count, max_pages, file_name, rate_limiter
        )
