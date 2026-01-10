#!/usr/bin/env python3
"""Worker Manager for MainWindow.

This module manages ProcessingWorker lifecycle and signal connections.
"""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QProgressBar

from philocr.ui.worker_callbacks import WorkerCallbacks
from philocr.workers.processing_worker import ProcessingWorker

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class WorkerManager:
    """Manages ProcessingWorker lifecycle and signal connections."""

    def __init__(
        self,
        temp_cleaner: Any,  # TempFileCleaner
        progress_bar: QProgressBar,
        callbacks: WorkerCallbacks,
    ) -> None:
        """Initialize the Worker Manager.

        Args:
            temp_cleaner: Temporary file cleaner instance
            progress_bar: Progress bar widget
            callbacks: WorkerCallbacks object containing all callback functions
        """
        self.temp_cleaner = temp_cleaner
        self.progress_bar = progress_bar
        self.callbacks = callbacks
        self.worker: ProcessingWorker | None = None

    def start_single_file_processing(self, file_path: str) -> None:
        """Start processing a single file.

        Args:
            file_path: Path to the PDF file to process
        """
        # Clear previews and set processing state
        self.callbacks.on_preview_clear()
        self.callbacks.on_text_update("Processing...")
        self._set_button_states_processing()

        # Set up progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)

        # Create and configure worker
        self.worker = ProcessingWorker(file_path, None, self.temp_cleaner)

        # Connect signals
        _ = self.worker.update_signal.connect(self.callbacks.on_text_update)
        _ = self.worker.status_signal.connect(self.callbacks.on_status_update)
        _ = self.worker.progress_signal.connect(self.progress_bar.setValue)
        _ = self.worker.error_signal.connect(self.callbacks.on_error)
        _ = self.worker.finished_signal.connect(self.callbacks.on_finished)
        _ = self.worker.json_ready_signal.connect(self.callbacks.on_json_ready)

        # Set metadata
        metadata = {
            "process_date": datetime.datetime.now().isoformat(),
            "mode": "single",
        }
        self.worker.set_metadata(metadata)

        # Start worker
        self.worker.start()

    def start_batch_processing(self, file_paths: list[str]) -> None:
        """Start batch processing multiple files.

        Args:
            file_paths: List of PDF file paths to process
        """
        # Clear previews and set processing state
        self.callbacks.on_preview_clear()
        self.callbacks.on_text_update(
            f"Selected {len(file_paths)} files for batch processing.\n"
        )
        self.callbacks.on_text_update(
            "Processing will respect Google's rate limits " "(15 requests/minute).\n"
        )
        self._set_button_states_processing()

        # Set up progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)

        # Create and configure worker
        self.worker = ProcessingWorker("", None, self.temp_cleaner)
        self.worker.set_batch_mode(file_paths)

        # Connect signals
        _ = self.worker.update_signal.connect(self.callbacks.on_text_update)
        _ = self.worker.status_signal.connect(self.callbacks.on_status_update)
        _ = self.worker.progress_signal.connect(self.progress_bar.setValue)
        _ = self.worker.error_signal.connect(self.callbacks.on_error)
        _ = self.worker.finished_signal.connect(self.callbacks.on_finished)
        _ = self.worker.json_ready_signal.connect(self.callbacks.on_json_ready)

        # Set metadata
        metadata = {
            "process_date": datetime.datetime.now().isoformat(),
            "mode": "batch",
            "file_count": len(file_paths),
        }
        self.worker.set_metadata(metadata)

        # Start worker
        self.worker.start()

    def _set_button_states_processing(self) -> None:
        """Set button states during processing."""
        self.callbacks.on_button_state_change(
            {
                "select": False,
                "batch": False,
                "save": False,
                "save_json": False,
                "save_html": False,
                "clear": False,
            }
        )

    def handle_completion(
        self,
        success: bool,
        has_text: bool,
        has_json: bool,
        current_json: dict[str, Any] | None,
    ) -> None:
        """Handle processing completion.

        Args:
            success: Whether processing was successful
            has_text: Whether text content is available
            has_json: Whether JSON data is available
            current_json: Current JSON result data
        """
        # Re-enable input buttons
        self.callbacks.on_button_state_change(
            {
                "select": True,
                "batch": True,
                "clear": True,
            }
        )

        # Enable save buttons based on content availability
        self.callbacks.on_button_state_change(
            {
                "save": success and has_text,
                "save_json": success and has_json,
                "save_html": success and has_json,
                "save_markdown": success and has_json,
            }
        )

        # Hide progress bar
        self.progress_bar.setVisible(False)

        # Schedule cleanup of old temporary files
        if self.temp_cleaner:
            _ = QTimer.singleShot(
                2000, lambda: self.temp_cleaner.clean_old_temp_files(24)
            )
