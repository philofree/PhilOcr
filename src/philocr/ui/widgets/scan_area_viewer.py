"""Scrollable viewer widget for selecting scan areas on all PDF pages."""

from __future__ import annotations

from pathlib import Path

# Image dimensions
RGB_DIMS = 3

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from philocr.models.scan_area import (
    ManualScanArea,
    ManualScanAreas,
    load_scan_areas,
    save_scan_areas,
)
from philocr.pipeline.utils.pdf_render import render_pdf_page
from philocr.ui.widgets.page_scan_widget import PageScanAreaWidget


class ScanAreaViewerWidget(QWidget):
    """Scrollable viewer for selecting scan areas on all PDF pages.

    Displays all pages in a vertical scrollable list, each with a
    draggable rectangle for defining the scan area.
    """

    scan_areas_saved = pyqtSignal(ManualScanAreas)
    process_requested = pyqtSignal(ManualScanAreas)

    def __init__(
        self,
        pdf_path: str,
        display_width: int = 400,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the scan area viewer.

        Args:
            pdf_path: Path to PDF file
            display_width: Width to display each page at
            parent: Parent widget
        """
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.display_width = display_width
        self.scan_areas = ManualScanAreas(areas={})
        self.page_widgets: dict[int, PageScanAreaWidget] = {}

        # Try to load existing scan areas
        self._load_existing_scan_areas()

        # Set up UI
        self._setup_ui()

        # Load and display pages
        self._load_pages()

    def _setup_ui(self) -> None:
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for pages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container widget for pages
        pages_container = QWidget()
        pages_layout = QVBoxLayout(pages_container)
        pages_layout.setSpacing(10)
        pages_layout.setContentsMargins(0, 0, 0, 0)
        pages_layout.addStretch()

        scroll_area.setWidget(pages_container)
        layout.addWidget(scroll_area)

        self.pages_container = pages_container
        self.pages_layout = pages_layout
        self.scroll_area = scroll_area

    def _load_existing_scan_areas(self) -> None:
        """Load existing scan areas from JSON file if it exists."""
        scan_areas_path = Path(self.pdf_path).with_suffix(".scan_areas.json")
        if scan_areas_path.exists():
            try:
                self.scan_areas = load_scan_areas(scan_areas_path)
            except Exception as e:
                # If loading fails, start with empty scan areas
                from philocr.utils.logging_config import get_logger

                logger = get_logger(__name__)
                logger.warning(
                    "scan_areas_load_failed",
                    path=str(scan_areas_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                self.scan_areas = ManualScanAreas(areas={})

    def _load_pages(self) -> None:
        """Load all pages from PDF and create widgets."""
        import fitz  # PyMuPDF

        doc = fitz.open(self.pdf_path)
        num_pages = len(doc)
        doc.close()

        for page_num in range(num_pages):
            try:
                # Render page at lower DPI for preview (faster)
                page_image = render_pdf_page(self.pdf_path, page_num, dpi=150)

                # Convert to grayscale if needed
                if len(page_image.shape) == RGB_DIMS:
                    from philocr.pipeline.utils.pdf_render import convert_to_grayscale

                    page_image = convert_to_grayscale(page_image)

                # Get existing scan area for this page if available
                existing_area = self.scan_areas.get(page_num)

                # Create page widget
                page_widget = PageScanAreaWidget(
                    page_num=page_num,
                    page_image=page_image,
                    initial_scan_area=existing_area,
                    display_width=self.display_width,
                )
                _ = page_widget.scan_area_changed.connect(self._on_scan_area_changed)

                # Create page container with page number, widget, and copy button
                page_container = QWidget()
                page_container_layout = QVBoxLayout(page_container)
                page_container_layout.setContentsMargins(0, 5, 0, 5)
                page_container_layout.setSpacing(5)

                # Page label and copy button row
                header_row = QWidget()
                header_layout = QHBoxLayout(header_row)
                header_layout.setContentsMargins(0, 0, 0, 0)
                header_layout.setSpacing(10)

                page_label = QLabel(f"Page {page_num + 1}")
                page_label.setStyleSheet("font-size: 12pt; color: #1e3a6e;")
                header_layout.addStretch()
                header_layout.addWidget(page_label)

                # Mask mode checkbox
                mask_checkbox = QCheckBox("Mask Mode (Draw Whiteout)")
                _ = mask_checkbox.toggled.connect(
                    lambda checked, w=page_widget: w.set_mask_mode(checked)
                )
                header_layout.addWidget(mask_checkbox)

                # Clear masks button
                clear_masks_button = QPushButton("Clear Masks")
                clear_masks_button.setMaximumWidth(100)
                _ = clear_masks_button.clicked.connect(
                    lambda checked, w=page_widget: w.clear_masks()
                )
                header_layout.addWidget(clear_masks_button)

                # Line break mode checkbox
                line_break_checkbox = QCheckBox("Line Break Mode")
                _ = line_break_checkbox.toggled.connect(
                    lambda checked, w=page_widget: w.set_line_break_mode(checked)
                )
                header_layout.addWidget(line_break_checkbox)

                # Clear line breaks button
                clear_lb_button = QPushButton("Clear Breaks")
                clear_lb_button.setMaximumWidth(100)
                _ = clear_lb_button.clicked.connect(
                    lambda checked, w=page_widget: w.clear_line_breaks()
                )
                header_layout.addWidget(clear_lb_button)

                # Paragraph break info label
                para_label = QLabel("Right-click = ¶ break")
                para_label.setStyleSheet("color: #008800; font-weight: bold;")
                header_layout.addWidget(para_label)

                # Clear paragraph breaks button
                clear_pb_button = QPushButton("Clear ¶")
                clear_pb_button.setMaximumWidth(80)
                _ = clear_pb_button.clicked.connect(
                    lambda checked, w=page_widget: w.clear_paragraph_breaks()
                )
                header_layout.addWidget(clear_pb_button)

                # Only add copy buttons if not the last page
                if page_num < num_pages - 1:
                    copy_button = QPushButton("Copy to Next →")
                    copy_button.setMaximumWidth(120)
                    _ = copy_button.clicked.connect(
                        lambda checked, p=page_num: self._copy_to_next_page(p)
                    )
                    header_layout.addWidget(copy_button)

                    copy_all_button = QPushButton("Copy to All Following →")
                    copy_all_button.setMaximumWidth(180)
                    _ = copy_all_button.clicked.connect(
                        lambda checked, p=page_num: self._copy_to_all_following(p)
                    )
                    header_layout.addWidget(copy_all_button)
                else:
                    header_layout.addStretch()

                page_container_layout.addWidget(header_row)

                # Center the page widget
                page_widget_container = QWidget()
                page_widget_layout = QHBoxLayout(page_widget_container)
                page_widget_layout.setContentsMargins(0, 0, 0, 0)
                page_widget_layout.addStretch()
                page_widget_layout.addWidget(page_widget)
                page_widget_layout.addStretch()

                page_container_layout.addWidget(page_widget_container)

                # Add to layout (before the stretch)
                self.pages_layout.insertWidget(
                    self.pages_layout.count() - 1, page_container
                )

                self.page_widgets[page_num] = page_widget

                # Update scan areas with current widget value
                self.scan_areas.set(page_num, page_widget.get_scan_area())

            except Exception as e:
                # Log error but continue with other pages
                from philocr.utils.logging_config import get_logger

                logger = get_logger(__name__)
                logger.error(
                    "page_load_failed",
                    page_num=page_num,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

    def _on_scan_area_changed(self, page_num: int, area: ManualScanArea) -> None:
        """Handle scan area change from a page widget.

        Args:
            page_num: Page number that changed
            area: New scan area
        """
        self.scan_areas.set(page_num, area)

    def _copy_to_next_page(self, page_num: int) -> None:
        """Copy scan area from current page to next page.

        Args:
            page_num: Source page number
        """
        # Get current page's scan area
        current_area = self.scan_areas.get(page_num)
        if current_area is None:
            return

        # Check if next page exists
        next_page_num = page_num + 1
        if next_page_num not in self.page_widgets:
            return

        # Copy to next page widget
        next_widget = self.page_widgets[next_page_num]
        next_widget.set_scan_area(current_area)

        # Update scan areas
        self.scan_areas.set(next_page_num, current_area)

    def _copy_to_all_following(self, page_num: int) -> None:
        """Copy scan area from current page to all following pages.

        Args:
            page_num: Source page number
        """
        # Get current page's scan area
        current_area = self.scan_areas.get(page_num)
        if current_area is None:
            return

        # Copy to all following pages
        for target_page in range(page_num + 1, len(self.page_widgets)):
            if target_page in self.page_widgets:
                target_widget = self.page_widgets[target_page]
                target_widget.set_scan_area(current_area)
                self.scan_areas.set(target_page, current_area)

    def save_scan_areas(self) -> None:
        """Save scan areas to JSON file and emit signal."""
        # Collect current scan areas from all widgets
        for page_num, widget in self.page_widgets.items():
            self.scan_areas.set(page_num, widget.get_scan_area())

        # Save to file
        scan_areas_path = Path(self.pdf_path).with_suffix(".scan_areas.json")
        try:
            save_scan_areas(self.scan_areas, scan_areas_path)
            self.scan_areas_saved.emit(self.scan_areas)

            # Show success message
            from PyQt6.QtWidgets import QMessageBox

            _ = QMessageBox.information(
                self,
                "Scan Areas Saved",
                f"Scan areas saved to:\n{scan_areas_path}",
            )
        except Exception as e:
            from philocr.utils.logging_config import get_logger

            logger = get_logger(__name__)
            logger.error(
                "scan_areas_save_failed",
                path=str(scan_areas_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            from PyQt6.QtWidgets import QMessageBox

            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            _ = QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save scan areas:\n{e}",
            )
            raise RuntimeError(f"CRITICAL: Scan areas save failed - {e}") from e

    def process_scan_areas(self) -> None:
        """Process scan areas.

        Collects current scan areas and emits process_requested signal.
        """
        # Ensure scan areas are saved first
        scan_areas = self.get_scan_areas()
        scan_areas_path = Path(self.pdf_path).with_suffix(".scan_areas.json")

        # Save to file if not already saved
        try:
            save_scan_areas(scan_areas, scan_areas_path)
        except Exception as e:
            from philocr.utils.logging_config import get_logger

            logger = get_logger(__name__)
            logger.error(
                "scan_areas_save_failed_before_process",
                path=str(scan_areas_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            from PyQt6.QtWidgets import QMessageBox

            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            _ = QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save scan areas before processing:\n{e}",
            )
            raise RuntimeError(
                f"CRITICAL: Scan areas save failed before process - {e}"
            ) from e

        # Emit process signal
        self.process_requested.emit(scan_areas)

    def get_scan_areas(self) -> ManualScanAreas:
        """Get current scan areas.

        Returns:
            Current ManualScanAreas
        """
        # Collect from all widgets
        for page_num, widget in self.page_widgets.items():
            self.scan_areas.set(page_num, widget.get_scan_area())
        return self.scan_areas
