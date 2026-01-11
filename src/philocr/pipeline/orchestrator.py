"""Pipeline orchestrator coordinating all processing stages."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.models.config import PipelineConfig
from philocr.models.document import Document, DocumentMetadata
from philocr.models.page import PageImage
from philocr.models.template import DocumentTemplate
from philocr.pipeline.stage1_normalise import normalise_all_pages
from philocr.pipeline.stage2_mask import apply_template_to_pages
from philocr.pipeline.stage2_template import extract_template
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
        self.on_progress = on_progress or (lambda *args: None)
        self.on_status = on_status or (lambda *args: None)
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
    ) -> Document:
        """Process a document through all pipeline stages.

        Args:
            pdf_path: Path to source PDF
            metadata: Optional document metadata
            project_id: Optional Google Cloud project ID
            location: Optional Document AI location
            processor_id: Optional Document AI processor ID

        Returns:
            Complete Document object

        Raises:
            Exception: If processing fails at any stage
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
        stage2_dir = self.output_base_dir / "stage2_masked"
        stage2_template_dir = self.output_base_dir / "stage2_template"

        # Stage 1: Image Normalisation
        self._emit_status("Stage 1: Normalising pages...")
        normalised_images = self._stage1_normalise(pdf_path, str(stage1_dir))

        # Stage 2a+2b: Template Extraction
        self._emit_status("Stage 2: Extracting template...")
        template = self._stage2_extract_template(
            normalised_images, str(stage2_template_dir)
        )

        # Stage 2c: Apply Masking
        self._emit_status("Stage 2: Applying template mask...")
        masked_pages = self._stage2_apply_masking(
            normalised_images, template, str(stage2_dir)
        )

        # Stage 3: OCR
        self._emit_status("Stage 3: Running OCR...")
        ocr_results = self._stage3_ocr(masked_pages, project_id, location, processor_id)

        # Stage 4: Assembly
        self._emit_status("Stage 4: Assembling text...")
        document = self._stage4_assemble(ocr_results, template, metadata)

        total_time = time.time() - start_time
        logger.info(
            "pipeline_completed",
            pdf_path=pdf_path,
            total_time=total_time,
            total_pages=len(normalised_images),
            template_confidence=template.confidence,
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

    def _stage2_extract_template(
        self,
        normalised_images: list[PageImage],
        output_dir: str,
    ) -> DocumentTemplate:
        """Execute Stage 2a+2b: Template extraction.

        Args:
            normalised_images: List of normalised page images
            output_dir: Output directory for template JSON

        Returns:
            DocumentTemplate object
        """
        from philocr.pipeline.stage2_template import (
            apply_conservative_defaults,
            get_default_template,
        )

        stage_start = time.time()

        self._emit_progress("Stage 2", 0, "Detecting zones on sample pages...")

        # Extract template with fallback for low confidence
        try:
            template = extract_template(normalised_images, self.config)

            if template.confidence < self.config.min_template_confidence:
                logger.warning(
                    "template_low_confidence",
                    confidence=template.confidence,
                    threshold=self.config.min_template_confidence,
                )
                if normalised_images:
                    template = apply_conservative_defaults(
                        template, normalised_images[0]
                    )
                else:
                    template = get_default_template()
        except Exception as e:
            logger.error(
                "template_extraction_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            template = get_default_template(
                normalised_images[0] if normalised_images else None
            )

        # Save template
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        template_path = Path(output_dir) / "template.json"
        template.to_json(str(template_path))

        self._emit_progress(
            "Stage 2",
            100,
            f"Template extracted (confidence: {template.confidence:.2f})",
        )

        stage_time = time.time() - stage_start
        self.stage_times["stage2"] = stage_time

        return template

    def _stage2_apply_masking(
        self,
        normalised_images: list[PageImage],
        template: DocumentTemplate,
        output_dir: str,
    ) -> list[Any]:  # list[MaskedPage] | list[CroppedPage]
        """Execute Stage 2c: Apply template masking.

        Args:
            normalised_images: List of normalised page images
            template: Document template
            output_dir: Output directory for masked images

        Returns:
            List of MaskedPage or CroppedPage objects
        """
        stage_start = time.time()
        total_pages = len(normalised_images)

        self._emit_progress(
            "Stage 2", 0, f"Applying template mask to {total_pages} pages..."
        )

        masked_pages = apply_template_to_pages(
            normalised_images, template, output_dir, self.config
        )

        # Update progress as we process (approximate)
        for i in range(total_pages):
            progress = int((i + 1) / total_pages * 100)
            self._emit_progress(
                "Stage 2",
                progress,
                f"Masked {i + 1}/{total_pages} pages",
            )

        self._emit_progress("Stage 2", 100, f"Masked {total_pages} pages")

        stage_time = time.time() - stage_start
        self.stage_times["stage2c"] = stage_time

        return masked_pages

    def _stage3_ocr(
        self,
        masked_pages: list[Any],  # list[MaskedPage] | list[CroppedPage]
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
    ) -> list[Any]:  # list[OCRResult]
        """Execute Stage 3: OCR on masked images.

        Args:
            masked_pages: List of masked/cropped pages
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
