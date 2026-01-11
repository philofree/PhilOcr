"""Integration tests for the full pipeline."""

from unittest.mock import patch

import pytest

from philocr.models.config import PipelineConfig
from philocr.models.document import DocumentMetadata
from philocr.pipeline.orchestrator import PipelineOrchestrator


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    @pytest.mark.integration()
    @patch("philocr.pipeline.orchestrator.get_pdf_page_count")
    @patch("philocr.pipeline.orchestrator.assemble_document")
    @patch("philocr.pipeline.orchestrator.ocr_all_pages")
    @patch("philocr.pipeline.orchestrator.apply_template_to_pages")
    @patch("philocr.pipeline.stage2_template.extract_template")
    @patch("philocr.pipeline.stage2_zones.detect_zones_for_template")
    @patch("philocr.pipeline.orchestrator.normalise_all_pages")
    def test_full_pipeline_integration(
        self,
        mock_normalise,
        mock_detect_zones,
        mock_extract_template,
        mock_apply_mask,
        mock_ocr,
        mock_assemble,
        mock_page_count,
        temp_dir,
    ):
        """Test the full pipeline flow with mocked dependencies."""
        config = PipelineConfig()
        orchestrator = PipelineOrchestrator(config, str(temp_dir))

        # Mock PDF page count
        mock_page_count.return_value = 10

        # Mock Stage 1: Normalisation
        from philocr.models.page import PageImage

        mock_normalised = [
            PageImage(
                page_num=i,
                path=f"page_{i}.png",
                dpi=300,
                width=1000,
                height=1500,
                skew_corrected=0.0,
            )
            for i in range(10)
        ]
        mock_normalise.return_value = mock_normalised

        # Mock Stage 2: Template extraction
        from philocr.models.page import PageZones
        from philocr.models.template import DocumentTemplate

        mock_zones = [
            PageZones(
                page_width=1000,
                page_height=1500,
                header_bottom=100,
                footer_top=1400,
                left_margin_right=100,
                right_margin_left=900,
                footnote_separator_y=None,
                body_left=100,
                body_right=900,
                body_top=100,
                body_bottom=1400,
            )
            for _ in range(5)
        ]
        mock_detect_zones.return_value = mock_zones

        mock_template = DocumentTemplate(
            page_width=1000,
            page_height=1500,
            body_left=100,
            body_right=900,
            body_top=100,
            body_bottom=1400,
            header_bottom=100,
            footer_top=1400,
            left_margin_right=100,
            right_margin_left=900,
            footnote_separator_y=None,
            pages_analysed=5,
            confidence=0.9,
            has_line_numbers_left=False,
            has_line_numbers_right=False,
            has_footnotes=False,
        )
        mock_extract_template.return_value = mock_template

        # Mock Stage 2c: Masking
        from philocr.models.bounding_box import BoundingBox
        from philocr.models.page import MaskedPage

        mock_masked = [
            MaskedPage(
                page_num=i,
                original_path=f"page_{i}.png",
                masked_path=f"masked_{i}.png",
                body_bounds=BoundingBox(x1=100, y1=100, x2=900, y2=1400),
            )
            for i in range(10)
        ]
        mock_apply_mask.return_value = mock_masked

        # Mock Stage 3: OCR
        from philocr.models.ocr_result import OCRResult

        mock_ocr_results = [
            OCRResult(
                page_num=i,
                text=f"Page {i} text content",
                confidence=0.95,
                blocks=[],
                paragraphs=[],
                lines=[],
            )
            for i in range(10)
        ]
        mock_ocr.return_value = mock_ocr_results

        # Mock Stage 4: Assembly
        from philocr.models.document import Document

        mock_document = Document(
            metadata=DocumentMetadata(
                title="Test Document",
                source_path="test.pdf",
            ),
            template=mock_template,
            pages=[],
            full_text="Complete document text",
            statistics=None,
        )
        mock_assemble.return_value = mock_document

        # Run pipeline
        metadata = DocumentMetadata(
            title="Test Document",
            source_path="test.pdf",
        )
        result = orchestrator.process_document(
            "test.pdf",
            metadata=metadata,
        )

        # Verify pipeline was called correctly
        assert isinstance(result, Document)
        mock_normalise.assert_called_once()
        mock_extract_template.assert_called_once()
        mock_apply_mask.assert_called_once()
        # ocr_all_pages is called once per page (10 times)
        assert mock_ocr.call_count == 10
        mock_assemble.assert_called_once()

    @pytest.mark.integration()
    def test_orchestrator_initialization(self, temp_dir):
        """Test that orchestrator initializes correctly."""
        config = PipelineConfig()
        orchestrator = PipelineOrchestrator(config, str(temp_dir))

        assert orchestrator.config == config
        assert orchestrator.output_base_dir.exists()
        assert isinstance(orchestrator.stage_times, dict)

    @pytest.mark.integration()
    def test_orchestrator_progress_callbacks(self, temp_dir):
        """Test that orchestrator calls progress callbacks."""
        config = PipelineConfig()
        progress_calls: list[tuple] = []
        status_calls: list[str] = []

        def on_progress(stage: str, progress: int, status: str) -> None:
            progress_calls.append((stage, progress, status))

        def on_status(message: str) -> None:
            status_calls.append(message)

        orchestrator = PipelineOrchestrator(
            config,
            str(temp_dir),
            on_progress=on_progress,
            on_status=on_status,
        )

        # Test progress emission
        orchestrator._emit_progress("Stage 1", 50, "Processing...")
        assert len(progress_calls) == 1
        assert progress_calls[0] == ("Stage 1", 50, "Processing...")

        # Test status emission
        orchestrator._emit_status("Test status")
        assert len(status_calls) == 1
        assert status_calls[0] == "Test status"
