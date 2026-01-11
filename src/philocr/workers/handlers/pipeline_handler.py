"""Pipeline handler for advanced pipeline processing mode."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.models.config import PipelineConfig
from philocr.models.document import Document, DocumentMetadata
from philocr.pipeline.orchestrator import PipelineOrchestrator
from philocr.utils.logging_config import get_logger

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    logger = get_logger(__name__)


class PipelineHandler:
    """Handler for advanced pipeline processing mode."""

    def __init__(
        self,
        config: PipelineConfig,
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
        on_text_update: Callable[[str], None],
        on_stage_progress: Callable[[str, int, str], None] | None = None,
        on_template_ready: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize the pipeline handler.

        Args:
            config: Pipeline configuration
            on_status_update: Callback for status messages
            on_progress_update: Callback for overall progress (0-100)
            on_text_update: Callback for text updates
            on_stage_progress: Optional callback for stage-specific progress
            on_template_ready: Optional callback when template is ready
        """
        self.config = config
        self.on_status_update = on_status_update
        self.on_progress_update = on_progress_update
        self.on_text_update = on_text_update
        self.on_stage_progress = on_stage_progress or (lambda *args: None)
        self.on_template_ready = on_template_ready or (lambda *args: None)

    def process_single_file(
        self,
        file_path: str,
        file_name: str,
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Process a single file through the pipeline.

        Args:
            file_path: Path to PDF file
            file_name: Name of the file
            project_id: Optional Google Cloud project ID
            location: Optional Document AI location
            processor_id: Optional Document AI processor ID

        Returns:
            Tuple of (extracted_text, document_json)
        """
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base_dir = Path(temp_dir) / "pipeline_output"

            # Create orchestrator with progress callbacks
            orchestrator = PipelineOrchestrator(
                config=self.config,
                output_base_dir=str(output_base_dir),
                on_progress=self._handle_progress,
                on_status=self.on_status_update,
            )

            # Generate metadata
            metadata = DocumentMetadata(
                title=file_name,
                source_path=file_path,
            )

            # Process document
            document = orchestrator.process_document(
                pdf_path=file_path,
                metadata=metadata,
                project_id=project_id,
                location=location,
                processor_id=processor_id,
            )

            # Emit template ready signal
            if self.on_template_ready:
                template_dict = {
                    "page_width": document.template.page_width,
                    "page_height": document.template.page_height,
                    "body_left": document.template.body_left,
                    "body_right": document.template.body_right,
                    "body_top": document.template.body_top,
                    "body_bottom": document.template.body_bottom,
                    "header_bottom": document.template.header_bottom,
                    "footer_top": document.template.footer_top,
                    "left_margin_right": document.template.left_margin_right,
                    "right_margin_left": document.template.right_margin_left,
                    "footnote_separator_y": document.template.footnote_separator_y,
                    "pages_analysed": document.template.pages_analysed,
                    "confidence": document.template.confidence,
                    "has_line_numbers_left": document.template.has_line_numbers_left,
                    "has_line_numbers_right": document.template.has_line_numbers_right,
                    "has_footnotes": document.template.has_footnotes,
                }
                self.on_template_ready(template_dict)

            # Update text as we process
            self.on_text_update(document.full_text)

            # Convert document to JSON format compatible with existing system
            document_json = self._document_to_json(document, orchestrator)

            return document.full_text, document_json

    def process_batch_files(
        self,
        file_paths: list[str],
        project_id: str | None = None,
        location: str | None = None,
        processor_id: str | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Process multiple files through the pipeline.

        Args:
            file_paths: List of PDF file paths
            project_id: Optional Google Cloud project ID
            location: Optional Document AI location
            processor_id: Optional Document AI processor ID

        Returns:
            Tuple of (combined_text, list of document_json dicts)
        """
        all_text = ""
        all_json_results: list[dict[str, Any]] = []

        total_files = len(file_paths)

        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)

            self.on_status_update(f"Processing {i+1} of {total_files}: {file_name}")

            try:
                file_text, file_json = self.process_single_file(
                    file_path,
                    file_name,
                    project_id,
                    location,
                    processor_id,
                )

                all_text += f"\n\n--- Document {i+1}: {file_name} ---\n\n"
                all_text += file_text
                all_json_results.append(file_json)

                self.on_text_update(all_text)

            except Exception as e:
                logger.error(
                    "batch_pipeline_error",
                    file_index=i + 1,
                    file_name=file_name,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                all_text += (
                    f"\n\n--- Document {i+1}: {file_name} " f"(ERROR: {str(e)}) ---\n\n"
                )
                self.on_text_update(all_text)

        return all_text, all_json_results

    def _handle_progress(
        self, stage_name: str, progress: int, status_text: str
    ) -> None:
        """Handle progress updates from orchestrator.

        Args:
            stage_name: Stage name
            progress: Progress percentage
            status_text: Status text
        """
        # Update stage-specific progress
        self.on_stage_progress(stage_name, progress, status_text)

        # Calculate overall progress (weighted by stage)
        # Stage 1: ~6%, Stage 2: ~8%, Stage 3: ~85%, Stage 4: ~1%
        overall_progress = self._calculate_overall_progress(stage_name, progress)
        self.on_progress_update(overall_progress)

    def _calculate_overall_progress(self, stage_name: str, stage_progress: int) -> int:
        """Calculate overall progress from stage progress.

        Args:
            stage_name: Current stage name
            stage_progress: Progress within current stage (0-100)

        Returns:
            Overall progress (0-100)
        """
        # Weight stages by estimated time (from architecture doc)
        # Stage 1: ~6%, Stage 2: ~8%, Stage 3: ~85%, Stage 4: ~1%
        if "Stage 1" in stage_name or "normalis" in stage_name.lower():
            base = 0
            weight = 6
        elif "Stage 2" in stage_name or "template" in stage_name.lower():
            base = 6
            weight = 8
        elif "Stage 3" in stage_name or "ocr" in stage_name.lower():
            base = 14
            weight = 85
        elif "Stage 4" in stage_name or "assembly" in stage_name.lower():
            base = 99
            weight = 1
        else:
            return stage_progress

        return min(100, base + int(stage_progress * weight / 100))

    def _document_to_json(
        self, document: Document, orchestrator: PipelineOrchestrator
    ) -> dict[str, Any]:
        """Convert Document to JSON format compatible with existing system.

        Args:
            document: Document object
            orchestrator: Orchestrator instance (for stage times)

        Returns:
            Dictionary in format expected by existing UI
        """
        # Build pages array similar to existing format
        pages: list[dict[str, Any]] = []
        for page_output in document.pages:
            page_dict: dict[str, Any] = {
                "page_number": page_output.page_num + 1,
                "text": page_output.full_text,
                "confidence": page_output.confidence,
            }

            # Add paragraphs if available
            if page_output.paragraphs:
                page_dict["paragraphs"] = [
                    {
                        "text": para.text,
                        "indent_class": para.indent_class,
                        "confidence": para.confidence,
                    }
                    for para in page_output.paragraphs
                ]

            # Add genre hint if available
            if page_output.genre_hint:
                page_dict["genre_hint"] = page_output.genre_hint.value
                page_dict["genre_confidence"] = page_output.genre_confidence

            pages.append(page_dict)

        # Build main document structure
        doc_json: dict[str, Any] = {
            "text": document.full_text,
            "pages": pages,
            "metadata": {
                "title": document.metadata.title,
                "source_path": document.metadata.source_path,
                "author": document.metadata.author,
                "edition": document.metadata.edition,
                "year": document.metadata.year,
                "pipeline_version": "1.4",
                "processing_mode": "advanced_pipeline",
            },
            "statistics": {
                "total_pages": document.statistics.total_pages,
                "total_paragraphs": document.statistics.total_paragraphs,
                "average_confidence": document.statistics.average_confidence,
                "pages_with_errors": document.statistics.pages_with_errors,
            },
            "template": {
                "confidence": document.template.confidence,
                "pages_analysed": document.template.pages_analysed,
                "body_bounds": {
                    "left": document.template.body_left,
                    "right": document.template.body_right,
                    "top": document.template.body_top,
                    "bottom": document.template.body_bottom,
                },
                "has_line_numbers_left": document.template.has_line_numbers_left,
                "has_line_numbers_right": document.template.has_line_numbers_right,
                "has_footnotes": document.template.has_footnotes,
            },
            "stages": orchestrator.stage_times,
        }

        return doc_json
