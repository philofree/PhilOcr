"""Processing orchestrator for coordinating document processing operations.

This module handles the orchestration of processing operations without UI
dependencies, allowing for better separation of concerns and testability.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.processing.document_ai import (
    MAX_REQUESTS_PER_MINUTE,
    RATE_LIMIT_SECONDS,
    RateLimiter,
)
from philocr.workers.handlers.batch_file_handler import BatchFileHandler
from philocr.workers.handlers.result_processor import ResultProcessor
from philocr.workers.handlers.single_file_handler import SingleFileHandler

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ProcessingOrchestrator:
    """Orchestrates document processing operations."""

    def __init__(
        self,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
        on_text_update: Callable[[str], None],
    ) -> None:
        """Initialize the processing orchestrator.

        Args:
            on_status_update: Callback for status updates
            on_progress_update: Callback for progress updates (0-100)
            on_text_update: Callback for text content updates
        """
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update
        self.on_text_update = on_text_update

        # Initialize handlers
        self.single_handler = SingleFileHandler(
            on_status_update=on_status_update,
            on_progress_update=on_progress_update,
            on_text_update=on_text_update,
        )
        self.batch_handler = BatchFileHandler(
            on_status_update=on_status_update,
            on_progress_update=on_progress_update,
        )
        self.result_processor = ResultProcessor()

        # Create rate limiter
        self.rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE, RATE_LIMIT_SECONDS)

    def process_single_file(
        self,
        file_path: str,
        max_pages: int = 15,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Process a single file and return results.

        Args:
            file_path: Path to the PDF file
            max_pages: Maximum pages per chunk
            metadata: Optional metadata to include in results

        Returns:
            Tuple of (extracted_text, result_json)
        """
        import os

        file_name = os.path.basename(file_path)
        self.on_status_update(f"Processing document: {file_name}")

        # Get page count
        page_count = self.single_handler.get_page_count(file_path)

        # Determine if splitting is needed
        if self.single_handler.should_split(page_count, max_pages):
            # For split processing, we still need ProcessingWorker's complex logic
            # This orchestrator provides a cleaner interface but delegates
            # complex split processing to the worker
            self.on_status_update(
                f"Document has {page_count} pages. Splitting required."
            )
            # Note: Actual split processing is still handled by ProcessingWorker
            # This orchestrator provides the coordination layer
            raise NotImplementedError(
                "Split processing should be handled by ProcessingWorker"
            )

        # Process normally
        extracted_text, document_layout = self.single_handler.process_document(
            file_path, file_name, self.rate_limiter, max_pages
        )

        # Build result JSON
        result_json = self.result_processor.build_result_json(
            text=extracted_text or "",
            document_layout=document_layout,
            metadata=metadata or {},
            file_name=file_name,
            page_count=page_count,
            chunks=1,
        )

        return extracted_text or "", result_json

    def prepare_batch_processing(
        self, file_paths: list[str], max_pages: int = 15
    ) -> int:
        """Prepare batch processing and return total expected chunks.

        Args:
            file_paths: List of file paths to process
            max_pages: Maximum pages per chunk

        Returns:
            Total number of chunks expected
        """
        total_chunks = self.batch_handler.count_total_chunks(file_paths, max_pages)
        self.on_status_update(
            f"Prepared batch processing: {len(file_paths)} files, "
            f"{total_chunks} total chunks"
        )
        return total_chunks

    def get_processing_metadata(
        self, mode: str, file_count: int | None = None
    ) -> dict[str, Any]:
        """Get processing metadata for a job.

        Args:
            mode: Processing mode ('single' or 'batch')
            file_count: Number of files (for batch mode)

        Returns:
            Metadata dictionary
        """
        metadata: dict[str, Any] = {
            "process_date": datetime.datetime.now().isoformat(),
            "mode": mode,
        }
        if file_count is not None:
            metadata["file_count"] = file_count
        return metadata
