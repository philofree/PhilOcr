"""Worker thread for processing PDFs to keep the UI responsive.

This module provides a thin QThread coordinator that delegates processing
logic to specialized handler classes.
"""

from __future__ import annotations

import os
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from philocr.processing.document_ai import (
    MAX_REQUESTS_PER_MINUTE,
    RATE_LIMIT_SECONDS,
    RateLimiter,
)
from philocr.utils.exceptions import PDFParseError, PDFProcessingError, WorkerError
from philocr.utils.logging_config import flush_loggers, get_logger
from philocr.workers.handlers.batch_file_handler import BatchFileHandler
from philocr.workers.handlers.result_processor import ResultProcessor
from philocr.workers.handlers.single_file_handler import SingleFileHandler
from philocr.workers.handlers.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class ProcessingWorker(QThread):
    """Worker thread for processing PDFs to keep the UI responsive."""

    update_signal = pyqtSignal(str)  # Signal for text updates
    status_signal = pyqtSignal(str)  # Signal for status updates
    progress_signal = pyqtSignal(int)  # Signal for progress updates
    error_signal = pyqtSignal(str)  # Signal for error messages
    finished_signal = pyqtSignal(bool)  # Signal for processing completion
    json_ready_signal = pyqtSignal(dict)  # Signal for JSON data ready

    def __init__(
        self,
        file_path: str,
        parent: Any | None = None,
        temp_cleaner: Any | None = None,
    ) -> None:
        """Initialize the ProcessingWorker.

        Args:
            file_path: Path to the PDF file to process
            parent: Parent QObject
            temp_cleaner: Temporary file cleaner utility
        """
        super().__init__(parent)
        self.file_path: str = file_path
        self.batch_mode: bool = False
        self.batch_files: list[str] = []
        self.stop_requested: bool = False
        self.result_text: str = ""
        self.result_json: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}

        # Initialize handlers
        temp_file_manager = TempFileManager(temp_cleaner)
        self.single_handler = SingleFileHandler(
            on_status_update=self.status_signal.emit,
            on_progress_update=self.progress_signal.emit,
            on_text_update=self.update_signal.emit,
            temp_file_manager=temp_file_manager,
        )
        self.batch_handler = BatchFileHandler(
            on_status_update=self.status_signal.emit,
            on_progress_update=self.progress_signal.emit,
            temp_file_manager=temp_file_manager,
        )
        self.result_processor = ResultProcessor()
        self.temp_file_manager = temp_file_manager

    def set_batch_mode(self, file_paths: list[str]) -> None:
        """Set up for batch processing.

        Args:
            file_paths: List of file paths to process in batch mode
        """
        self.batch_mode = True
        self.batch_files = file_paths

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set metadata for the processing job.

        Args:
            metadata: Metadata dictionary for the job
        """
        self.metadata = metadata

    def run(self) -> None:
        """Process the PDF file(s) and emit results."""
        rate_limiter: Any = RateLimiter(MAX_REQUESTS_PER_MINUTE, RATE_LIMIT_SECONDS)

        try:
            if self.batch_mode:
                self._process_batch_delegated(rate_limiter)
            else:
                self._process_single_delegated(rate_limiter)

            # Clean up any temporary files
            if self.temp_file_manager.temp_cleaner:
                self.temp_file_manager.temp_cleaner.clean_registered_files()

            self.finished_signal.emit(True)

        except (PDFProcessingError, PDFParseError, WorkerError) as e:
            logger.error(
                "document_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
        except Exception as e:
            # Catch-all for unexpected errors - log and re-raise as WorkerError
            logger.error(
                "unexpected_worker_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            worker_error = WorkerError(f"Unexpected error during processing: {e}")
            self.error_signal.emit(str(worker_error))
            self.finished_signal.emit(False)

    def _process_single_delegated(self, rate_limiter: Any) -> None:
        """Process a single PDF file by delegating to handlers.

        Args:
            rate_limiter: Rate limiter instance for API calls
        """
        try:
            file_name = os.path.basename(self.file_path)
            self.status_signal.emit(f"Processing document: {file_name}")
            logger.debug(
                "document_processing_started",
                file_path=self.file_path,
                file_name=file_name,
            )

            page_count = self.single_handler.get_page_count(self.file_path)
            max_pages = 15

            if self.single_handler.should_split(page_count, max_pages):
                # Process split document
                all_text, document_layout, total_chunks = (
                    self.single_handler.process_split_document(
                        self.file_path,
                        page_count,
                        max_pages,
                        file_name,
                        rate_limiter,
                    )
                )
                extracted_text = all_text
            else:
                # Process single document
                extracted_text, document_layout = self.single_handler.process_document(
                    self.file_path, file_name, rate_limiter, max_pages
                )
                total_chunks = 1

            # Build text from layout if needed
            if not extracted_text and document_layout:
                extracted_text = self.result_processor.build_text_from_layout(
                    document_layout
                )

            if extracted_text:
                self.update_signal.emit(extracted_text)
            else:
                self.update_signal.emit("No text extracted from document.")

            if total_chunks > 1:
                self.status_signal.emit(
                    f"Completed. Processed {page_count} pages in {total_chunks} chunks."
                )
            else:
                self.status_signal.emit(f"Completed. Processed {page_count} pages.")

            # Finalize results
            self.result_text = extracted_text or ""
            self.result_json = self.result_processor.finalize_single_result(
                text=extracted_text or "",
                document_layout=document_layout,
                metadata=self.metadata,
                file_name=file_name,
                page_count=page_count,
                chunks=total_chunks,
                on_json_ready=self.json_ready_signal.emit,
                on_progress_update=self.progress_signal.emit,
            )

        except (PDFProcessingError, PDFParseError) as e:
            # Handle PDF processing exceptions
            logger.error(
                "single_document_processing_error",
                file_path=self.file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.error_signal.emit(str(e))
            flush_loggers()
            raise
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                "single_document_processing_unexpected_error",
                file_path=self.file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            worker_error = WorkerError(f"Unexpected error processing document: {e}")
            self.error_signal.emit(str(worker_error))
            flush_loggers()
            raise worker_error from e

    def _process_batch_delegated(self, rate_limiter: Any) -> None:
        """Process multiple PDF files in batch mode by delegating to handlers.

        Args:
            rate_limiter: Rate limiter instance for API calls
        """
        from philocr.utils.json_handler import JSONHandler

        all_text = ""
        all_json_results: list[dict[str, Any]] = []
        max_pages = 15

        try:
            total_files = len(self.batch_files)
            total_chunks = self.batch_handler.count_total_chunks(
                self.batch_files, max_pages
            )

            logger.debug(
                "batch_processing_started",
                total_files=total_files,
                total_chunks=total_chunks,
            )

            processed_chunks = 0

            for i, file_path in enumerate(self.batch_files):
                file_name = os.path.basename(file_path)
                page_count = 0

                try:
                    page_count = self.single_handler.get_page_count(file_path)

                    self.status_signal.emit(
                        f"Processing {i+1} of {total_files}: {file_name} "
                        f"({page_count} pages)"
                    )

                    base_progress = int((processed_chunks / total_chunks) * 100)
                    self.progress_signal.emit(base_progress)

                    file_metadata = {
                        "filename": file_name,
                        "page_count": page_count,
                        "file_index": i + 1,
                        "total_files": total_files,
                    }

                    if page_count > max_pages:
                        file_text, document_layout, processed_chunks = (
                            self.batch_handler.process_split_file_in_batch(
                                file_path,
                                i,
                                total_files,
                                page_count,
                                max_pages,
                                rate_limiter,
                                processed_chunks,
                                total_chunks,
                            )
                        )
                    else:
                        file_text, document_layout, processed_chunks = (
                            self.batch_handler.process_single_file_in_batch(
                                file_path,
                                i,
                                total_files,
                                rate_limiter,
                                processed_chunks,
                                total_chunks,
                                max_pages,
                            )
                        )
                        file_metadata["chunks"] = 1

                    all_text += (
                        f"\n\n--- Document {i+1}: {file_name} "
                        f"({page_count} pages) ---\n\n"
                    )
                    all_text += file_text

                    file_json = JSONHandler.text_to_json(
                        file_text, file_metadata, document_layout or {}
                    )
                    all_json_results.append(file_json)
                    self.update_signal.emit(all_text)

                except (PDFProcessingError, PDFParseError, ValueError) as e:
                    logger.error(
                        "batch_file_error",
                        file_index=i + 1,
                        file_name=file_name,
                        file_path=file_path,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True,
                    )
                    error_text, processed_chunks = self.batch_handler.handle_file_error(
                        i,
                        file_name,
                        page_count,
                        max_pages,
                        e,
                        processed_chunks,
                        total_chunks,
                        self.progress_signal.emit,
                    )
                    all_text += error_text
                except Exception as e:
                    # Catch unexpected errors - log and handle gracefully
                    logger.error(
                        "batch_file_unexpected_error",
                        file_index=i + 1,
                        file_name=file_name,
                        file_path=file_path,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True,
                    )
                    worker_error = WorkerError(
                        f"Unexpected error processing {file_name}: {e}"
                    )
                    error_text, processed_chunks = self.batch_handler.handle_file_error(
                        i,
                        file_name,
                        page_count,
                        max_pages,
                        worker_error,
                        processed_chunks,
                        total_chunks,
                        self.progress_signal.emit,
                    )
                    all_text += error_text
                    self.update_signal.emit(all_text)

            # Finalize batch results
            self.result_text = all_text
            self.result_json = self.result_processor.finalize_batch_result(
                all_text=all_text,
                all_json_results=all_json_results,
                metadata=self.metadata,
                total_files=total_files,
                total_chunks=total_chunks,
                on_json_ready=self.json_ready_signal.emit,
                on_status_update=self.status_signal.emit,
                on_progress_update=self.progress_signal.emit,
            )

        except (PDFProcessingError, PDFParseError, WorkerError) as e:
            total_files_var = len(self.batch_files)
            logger.error(
                "batch_processing_error",
                total_files=total_files_var,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise
        except Exception as e:
            total_files_var = len(self.batch_files)
            logger.error(
                "batch_processing_unexpected_error",
                total_files=total_files_var,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            worker_error = WorkerError(f"Unexpected error during batch processing: {e}")
            flush_loggers()
            raise worker_error from e
