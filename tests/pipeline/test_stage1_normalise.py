"""Tests for Stage 1: Image normalization."""

from unittest.mock import patch

import numpy as np
import pytest

from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage
from philocr.pipeline.stage1_normalise import normalise_all_pages, normalise_page


class TestNormalisePage:
    """Test suite for normalise_page function."""

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.save_image")
    @patch("philocr.pipeline.stage1_normalise.rotate_image")
    @patch("philocr.pipeline.stage1_normalise.detect_skew")
    @patch("philocr.pipeline.stage1_normalise.convert_to_grayscale")
    @patch("philocr.pipeline.stage1_normalise.render_pdf_page")
    def test_normalise_page_no_skew(
        self,
        mock_render,
        mock_grayscale,
        mock_detect_skew,
        mock_rotate,
        mock_save,
        temp_dir,
    ):
        """Test normalizing a page with no skew."""
        config = PipelineConfig(deskew_threshold=0.1, target_dpi=300)
        mock_image = np.zeros((100, 150), dtype=np.uint8)
        mock_render.return_value = mock_image
        mock_grayscale.return_value = mock_image
        mock_detect_skew.return_value = 0.05  # Below threshold
        mock_rotate.return_value = mock_image

        result = normalise_page("test.pdf", 0, str(temp_dir), config)

        assert isinstance(result, PageImage)
        assert result.page_num == 0
        assert result.dpi == 300
        assert result.skew_corrected == 0.0
        mock_save.assert_called_once()

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.save_image")
    @patch("philocr.pipeline.stage1_normalise.rotate_image")
    @patch("philocr.pipeline.stage1_normalise.detect_skew")
    @patch("philocr.pipeline.stage1_normalise.convert_to_grayscale")
    @patch("philocr.pipeline.stage1_normalise.render_pdf_page")
    def test_normalise_page_with_skew(
        self,
        mock_render,
        mock_grayscale,
        mock_detect_skew,
        mock_rotate,
        mock_save,
        temp_dir,
    ):
        """Test normalizing a page with skew correction."""
        config = PipelineConfig(deskew_threshold=0.1, target_dpi=300)
        mock_image = np.zeros((100, 150), dtype=np.uint8)
        rotated_image = np.zeros((100, 150), dtype=np.uint8)
        mock_render.return_value = mock_image
        mock_grayscale.return_value = mock_image
        mock_detect_skew.return_value = 2.5  # Above threshold
        mock_rotate.return_value = rotated_image

        result = normalise_page("test.pdf", 0, str(temp_dir), config)

        assert isinstance(result, PageImage)
        assert result.skew_corrected == 2.5
        mock_rotate.assert_called_once()
        mock_save.assert_called_once()

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.save_image")
    @patch("philocr.pipeline.stage1_normalise.rotate_image")
    @patch("philocr.pipeline.stage1_normalise.detect_skew")
    @patch("philocr.pipeline.stage1_normalise.convert_to_grayscale")
    @patch("philocr.pipeline.stage1_normalise.render_pdf_page")
    def test_normalise_page_creates_output_path(
        self,
        mock_render,
        mock_grayscale,
        mock_detect_skew,
        mock_rotate,
        mock_save,
        temp_dir,
    ):
        """Test that output path is created correctly."""
        config = PipelineConfig(target_dpi=300)
        mock_image = np.zeros((100, 150), dtype=np.uint8)
        mock_render.return_value = mock_image
        mock_grayscale.return_value = mock_image
        mock_detect_skew.return_value = 0.0

        result = normalise_page("test.pdf", 5, str(temp_dir), config)

        expected_path = temp_dir / "page_0005.png"
        assert result.path == str(expected_path)


class TestNormaliseAllPages:
    """Test suite for normalise_all_pages function."""

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.normalise_page")
    def test_normalise_all_pages_parallel(
        self,
        mock_normalise_page,
    ):
        """Test normalizing multiple pages in parallel."""
        config = PipelineConfig(stage1_parallel_workers=2)
        mock_normalise_page.side_effect = lambda pdf, page, out, cfg: PageImage(
            page_num=page,
            path=f"page_{page}.png",
            dpi=300,
            width=100,
            height=150,
            skew_corrected=0.0,
        )

        results = normalise_all_pages("test.pdf", range(5), "/tmp/output", config)

        assert len(results) == 5
        assert mock_normalise_page.call_count == 5
        # Verify all page numbers are correct
        for i, result in enumerate(results):
            assert result.page_num == i

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.normalise_page")
    def test_normalise_all_pages_single(
        self,
        mock_normalise_page,
    ):
        """Test normalizing a single page."""
        config = PipelineConfig()
        mock_normalise_page.return_value = PageImage(
            page_num=0,
            path="page_0000.png",
            dpi=300,
            width=100,
            height=150,
            skew_corrected=0.0,
        )

        results = normalise_all_pages("test.pdf", range(1), "/tmp/output", config)

        assert len(results) == 1
        assert results[0].page_num == 0

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage1_normalise.normalise_page")
    def test_normalise_all_pages_empty_range(
        self,
        mock_normalise_page,
    ):
        """Test normalizing with empty page range."""
        config = PipelineConfig()
        results = normalise_all_pages("test.pdf", range(0), "/tmp/output", config)
        assert len(results) == 0
        mock_normalise_page.assert_not_called()
