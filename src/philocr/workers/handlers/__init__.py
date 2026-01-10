"""Worker handlers for processing operations.

This module contains handlers that extract business logic from the ProcessingWorker,
allowing for better separation of concerns and testability.
"""

from __future__ import annotations

from philocr.workers.handlers.batch_file_handler import BatchFileHandler
from philocr.workers.handlers.result_processor import ResultProcessor
from philocr.workers.handlers.single_file_handler import SingleFileHandler

__all__ = [
    "SingleFileHandler",
    "BatchFileHandler",
    "ResultProcessor",
]
