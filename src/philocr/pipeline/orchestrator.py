"""Pipeline orchestrator coordinating all processing stages."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from philocr.models.config import PipelineConfig
    from philocr.models.page import PageImage
else:
    from collections.abc import Callable

    from philocr.models.config import PipelineConfig
    from philocr.models.page import PageImage

from philocr.models.document import Document, DocumentMetadata
from philocr.models.template import DocumentTemplate
from philocr.pipeline.stage1_normalise import normalise_all_pages
from philocr.pipeline.stage2_mask import apply_zones_to_pages
from philocr.pipeline.stage3_ocr import ocr_all_pages
from philocr.pipeline.stage4_assemble import assemble_document, assemble_page
from philocr.processing.document_ai import RateLimiter
from philocr.processing.pdf_utils import get_pdf_page_count

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def _get_default_template(sample_image: PageImage | None = None) -> DocumentTemplate:
    """Create a default template for manual scan area mode.

    Args:
        sample_image: Optional sample image to get dimensions from

    Returns:
        DocumentTemplate with default values
    """
    # Use sample image dimensions if available, otherwise use typical 8.5x11 at 300 DPI
    if sample_image:
        page_width = sample_image.width
        page_height = sample_image.height
    else:
        # Default: 8.5 x 11 inches at 300 DPI
        page_width = 2550
        page_height = 3300

    # Full page bounds (manual scan areas handle the actual cropping)
    return DocumentTemplate(
        page_width=page_width,
        page_height=page_height,
        body_left=0,
        body_right=page_width,
        body_top=0,
        body_bottom=page_height,
        header_bottom=0,
        footer_top=page_height,
        left_margin_right=0,
        right_margin_left=page_width,
        footnote_separator_y=None,
        pages_analysed=0,
        confidence=1.0,  # Manual mode - user defined
        has_line_numbers_left=False,
        has_line_numbers_right=False,
        has_footnotes=False,
    )


class PipelineOrchestrator:
    """Coordinates all pipeline stages with progress tracking and error handling."""

    def __init__(
        self,
        config: PipelineConfig,
        output_base_dir: str,
        on_progress: Callable[[str, int, str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the pipeline orchestrator.

        Args:
            config: Pipeline configuration
            output_base_dir: Base directory for all stage outputs
            on_progress: Optional callback for progress updates
                        (stage_name, progress_percent, status_text)
            on_status: Optional callback for status messages
        """
        self.config = config
        self.output_base_dir = Path(output_base_dir)
        self.on_progress = on_progress or (lambda *_args: None)
        self.on_status = on_status or (lambda *_args: None)
        self.stage_times: dict[str, float] = {}

    def _emit_progress(self, stage_name: str, progress: int, status_text: str) -> None:
        """Emit progress update.

        Args:
            stage_name: Name of the stage
            progress: Progress percentage (0-100)
            status_text: Status message
        """
        self.on_progress(stage_name, progress, status_text)

    def _emit_status(self, message: str) -> None:
        """Emit status message.

        Args:
            message: Status message
        """
        self.on_status(message)

    def process_document(
        self,
        pdf_path: str,
        metadata: DocumentMetadata | None = None,
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
        manual_scan_areas: Any | None = None,  # ManualScanAreas
    ) -> Document:
        """Process a document through all pipeline stages.

        Args:
            pdf_path: Path to source PDF
            metadata: Optional document metadata
            project_id: Optional Google Cloud project ID
            location: Optional Document AI location
            processor_id: Optional Document AI processor ID
            manual_scan_areas: Manual scan areas defined by user (required)

        Returns:
            Complete Document object

        Raises:
            RuntimeError: If manual_scan_areas is not provided
        """
        start_time = time.time()

        # Generate metadata if not provided
        if metadata is None:
            metadata = DocumentMetadata(
                title=os.path.basename(pdf_path),
                source_path=pdf_path,
            )

        # Create output directories
        stage1_dir = self.output_base_dir / "stage1_normalised"
        stage2_dir = self.output_base_dir / "stage2_cropped"

        # Stage 1: Image Normalisation
        self._emit_status("Stage 1: Normalising pages...")
        normalised_images = self._stage1_normalise(pdf_path, str(stage1_dir))

        # Create default template (manual scan areas handle actual cropping)
        sample_image = normalised_images[0] if normalised_images else None
        template = _get_default_template(sample_image)

        if manual_scan_areas:
            logger.info(
                "using_manual_scan_areas",
                page_count=len(manual_scan_areas.areas),
            )

        # Stage 2: Apply Manual Scan Areas (crop to user-defined regions)
        self._emit_status("Stage 2: Cropping to scan areas...")
        cropped_pages = self._stage2_apply_cropping(
            normalised_images, str(stage2_dir), manual_scan_areas
        )

        # Stage 3: OCR
        self._emit_status("Stage 3: Running OCR...")
        ocr_results = self._stage3_ocr(
            cropped_pages, project_id, location, processor_id
        )

        # Stage 4: Assembly
        self._emit_status("Stage 4: Assembling text...")
        document = self._stage4_assemble(ocr_results, template, metadata)

        total_time = time.time() - start_time
        logger.info(
            "pipeline_completed",
            pdf_path=pdf_path,
            total_time=total_time,
            total_pages=len(normalised_images),
        )

        return document

    def _stage1_normalise(self, pdf_path: str, output_dir: str) -> list[PageImage]:
        """Execute Stage 1: Image normalisation.

        Args:
            pdf_path: Path to source PDF
            output_dir: Output directory for normalised images

        Returns:
            List of PageImage objects
        """
        stage_start = time.time()

        # Get page count
        page_count = get_pdf_page_count(pdf_path)
        page_range = range(page_count)

        self._emit_progress("Stage 1", 0, f"Normalising {page_count} pages...")

        # Normalise all pages (parallel processing)
        images = normalise_all_pages(pdf_path, page_range, output_dir, self.config)

        self._emit_progress("Stage 1", 100, f"Normalised {len(images)} pages")

        stage_time = time.time() - stage_start
        self.stage_times["stage1"] = stage_time

        return images

    def _stage2_apply_cropping(
        self,
        normalised_images: list[PageImage],
        output_dir: str,
        manual_scan_areas: Any | None = None,  # ManualScanAreas
    ) -> list[Any]:  # list[MaskedPage] | list[CroppedPage]
        """Execute Stage 2: Apply manual scan areas (crop to user-defined regions).

        Args:
            normalised_images: List of normalised page images
            output_dir: Output directory for cropped images
            manual_scan_areas: Manual scan areas for pages

        Returns:
            List of CroppedPage objects
        """
        stage_start = time.time()
        total_pages = len(normalised_images)

        self._emit_progress("Stage 2", 0, f"Cropping {total_pages} pages...")

        cropped_pages = apply_zones_to_pages(
            normalised_images, output_dir, self.config, manual_scan_areas
        )

        self._emit_progress("Stage 2", 100, f"Cropped {total_pages} pages")

        stage_time = time.time() - stage_start
        self.stage_times["stage2"] = stage_time

        return cropped_pages

    def _stage3_ocr(
        self,
        masked_pages: list[Any],  # list[MaskedPage] | list[CroppedPage]
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
    ) -> list[Any]:  # list[OCRResult]
        """Execute Stage 3: OCR on cropped images.

        Args:
            masked_pages: List of cropped pages
            project_id: Optional Google Cloud project ID
            location: Optional Document AI location
            processor_id: Optional Document AI processor ID

        Returns:
            List of OCRResult objects
        """
        from philocr.models.ocr_result import OCRResult

        stage_start = time.time()
        total_pages = len(masked_pages)

        self._emit_progress("Stage 3", 0, f"Running OCR on {total_pages} pages...")

        # Create rate limiter
        rate_limiter = RateLimiter(self.config.ocr_rate_limit_per_minute, 60.0)

        # Process OCR with progress updates
        ocr_results: list[OCRResult] = []
        for i, page in enumerate(masked_pages):
            result = ocr_all_pages(
                [page],
                rate_limiter,
                self.config,
                project_id,
                location,
                processor_id,
            )
            ocr_results.extend(result)

            progress = int((i + 1) / total_pages * 100)
            self._emit_progress(
                "Stage 3",
                progress,
                f"OCR'd {i + 1}/{total_pages} pages",
            )

        self._emit_progress("Stage 3", 100, f"OCR'd {total_pages} pages")

        stage_time = time.time() - stage_start
        self.stage_times["stage3"] = stage_time

        return ocr_results

    def _stage4_assemble(
        self,
        ocr_results: list[Any],  # list[OCRResult]
        template: DocumentTemplate,
        metadata: DocumentMetadata,
    ) -> Document:
        """Execute Stage 4: Text assembly.

        Args:
            ocr_results: List of OCR results
            template: Document template
            metadata: Document metadata

        Returns:
            Complete Document object
        """
        from philocr.models.ocr_result import OCRResult

        stage_start = time.time()
        total_pages = len(ocr_results)

        self._emit_progress("Stage 4", 0, f"Assembling {total_pages} pages...")

        # Assemble each page
        page_outputs = []
        for i, ocr_result in enumerate(ocr_results):
            if isinstance(ocr_result, OCRResult):
                page_output = assemble_page(ocr_result, self.config)
                page_outputs.append(page_output)

                progress = int((i + 1) / total_pages * 100)
                self._emit_progress(
                    "Stage 4",
                    progress,
                    f"Assembled {i + 1}/{total_pages} pages",
                )

        # Assemble full document
        document = assemble_document(page_outputs, template, metadata)

        self._emit_progress("Stage 4", 100, f"Assembled {total_pages} pages")

        stage_time = time.time() - stage_start
        self.stage_times["stage4"] = stage_time

        return document
