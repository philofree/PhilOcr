#!/usr/bin/env python3
"""Scan Area Manager for MainWindow.

This module manages scan area viewer display and processing coordination,
extracting scan area-related functionality from MainWindow.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTabWidget, QWidget

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ScanAreaManager:
    """Manages scan area viewer and processing coordination.

    Handles display of scan area viewer widget, signal connections,
    and processing coordination for manual scan areas.
    """

    def __init__(
        self,
        scan_area_tab: QWidget,  # noqa: F821
        tab_widget: QTabWidget,  # noqa: F821
        worker_manager: Any,  # WorkerManager
        on_status_update: Any,  # Callable[[str], None]
        on_error: Any,  # Callable[[str], None]
        on_scan_areas_changed: Any,  # Callable[[ManualScanAreas], None]
        get_processing_mode: Any,  # Callable[[], str]
        get_current_pdf_path: Any,  # Callable[[], str | None]
    ) -> None:
        """Initialize the Scan Area Manager.

        Args:
            scan_area_tab: Scan area tab widget container
            tab_widget: Tab widget for switching tabs
            worker_manager: Worker manager for processing
            on_status_update: Callback for status message updates
            on_error: Callback for error messages
            on_scan_areas_changed: Callback when scan areas change
            get_processing_mode: Callback to get processing mode
            get_current_pdf_path: Callback to get current PDF path
        """
        self.scan_area_tab = scan_area_tab
        self.tab_widget = tab_widget
        self.worker_manager = worker_manager
        self.on_status_update = on_status_update
        self.on_error = on_error
        self.on_scan_areas_changed = on_scan_areas_changed
        self.get_processing_mode = get_processing_mode
        self.get_current_pdf_path = get_current_pdf_path
        self.current_viewer: Any | None = None  # ScanAreaViewerWidget

    def show_scan_area_viewer(self, pdf_path: str) -> None:
        """Show scan area viewer in the scan area tab.

        Displays PDF pages with draggable scan area rectangles.
        Preserves all page image rendering and text display functionality.

        Args:
            pdf_path: Path to PDF file
        """
        from PyQt6.QtWidgets import QVBoxLayout

        from philocr.ui.widgets.scan_area_viewer import ScanAreaViewerWidget

        # Clear existing content from scan area tab
        layout = self.scan_area_tab.layout()

        if layout:
            # Remove all existing widgets
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Reuse existing layout instead of creating new one
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            layout = QVBoxLayout(self.scan_area_tab)
            layout.setContentsMargins(0, 0, 0, 0)

        # Create and add scan area viewer
        # This widget displays PDF pages with preview images and text
        viewer = ScanAreaViewerWidget(pdf_path, display_width=600)
        viewer.scan_areas_saved.connect(self.on_scan_areas_saved)
        viewer.process_requested.connect(
            lambda scan_areas: self.on_process_requested(scan_areas, pdf_path)
        )

        layout.addWidget(viewer)
        self.current_viewer = viewer

        # Switch to scan area tab
        scan_area_tab_index = None
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.scan_area_tab:
                scan_area_tab_index = i
                break

        if scan_area_tab_index is not None:
            self.tab_widget.setCurrentIndex(scan_area_tab_index)

        self.on_status_update("Select scan areas for each page")

    def on_scan_areas_saved(self, scan_areas: Any) -> None:  # ManualScanAreas
        """Handle scan areas saved signal.

        Args:
            scan_areas: ManualScanAreas that were saved
        """
        self.on_scan_areas_changed(scan_areas)
        self.on_status_update(
            "Scan areas saved. Click 'Process with Saved Scan Areas' to start OCR."
        )

    def on_process_requested(
        self, scan_areas: Any, pdf_path: str  # ManualScanAreas
    ) -> None:
        """Handle process requested signal.

        Starts processing with the saved scan areas (only if Manual Scan Area
        mode is selected).

        Args:
            scan_areas: ManualScanAreas to use for processing
            pdf_path: Path to PDF file
        """
        processing_mode = self.get_processing_mode()

        # Only use manual scan areas in Manual Scan Area mode
        if processing_mode == "advanced_pipeline":
            self.on_status_update("Starting processing with saved scan areas...")
        else:
            self.on_status_update("Starting standard OCR processing...")

        # Start processing
        current_pdf_path = self.get_current_pdf_path()
        if current_pdf_path:
            self.worker_manager.start_single_file_processing(
                current_pdf_path,
                processing_mode=processing_mode,
                manual_scan_areas=(
                    scan_areas if processing_mode == "advanced_pipeline" else None
                ),
            )
        else:
            self.on_error("No PDF file selected. Please select a PDF first.")

    def save_scan_areas(self) -> None:
        """Save scan areas from current viewer.

        Triggers save operation on the current scan area viewer if available.
        """
        if self.current_viewer:
            self.current_viewer.save_scan_areas()
        else:
            self.on_error("No scan area viewer is currently active.")

    def process_scan_areas(self) -> None:
        """Process scan areas from current viewer.

        Triggers process operation on the current scan area viewer if available.
        """
        if self.current_viewer:
            self.current_viewer.process_scan_areas()
        else:
            self.on_error("No scan area viewer is currently active.")
