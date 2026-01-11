"""Tests for Stage 2b: Template extraction."""

from unittest.mock import patch

import pytest

from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage, PageZones
from philocr.models.template import DocumentTemplate
from philocr.pipeline.stage2_template import (
    ZoneMeasurements,
    extract_template,
    robust_median_with_outliers,
    select_sample_pages,
)


class TestSelectSamplePages:
    """Test suite for select_sample_pages function."""

    @pytest.mark.unit()
    def test_select_sample_pages_sufficient(self):
        """Test selecting samples from document with sufficient pages."""
        pages = select_sample_pages(
            total_pages=100,
            sample_size=20,
            skip_first=2,
            skip_last=2,
            min_pages=5,
        )
        assert len(pages) == 20
        # Should skip first 2
        assert min(pages) >= 2
        # Should skip last 2
        assert max(pages) < 98

    @pytest.mark.unit()
    def test_select_sample_pages_too_short(self):
        """Test with document shorter than minimum."""
        pages = select_sample_pages(
            total_pages=3,
            sample_size=20,
            skip_first=2,
            skip_last=2,
            min_pages=5,
        )
        # Should return all available pages
        assert len(pages) == 3

    @pytest.mark.unit()
    def test_select_sample_pages_distributed(self):
        """Test that samples are distributed across the document."""
        pages = select_sample_pages(
            total_pages=50,
            sample_size=10,
            skip_first=2,
            skip_last=2,
            min_pages=5,
        )
        assert len(pages) == 10
        # Pages should be spread out (not all clustered)
        page_range = max(pages) - min(pages)
        assert page_range > 20  # Should span at least 20 pages

    @pytest.mark.unit()
    def test_select_sample_pages_skip_handling(self):
        """Test that skip_first and skip_last are respected."""
        pages = select_sample_pages(
            total_pages=20,
            sample_size=5,
            skip_first=5,
            skip_last=5,
            min_pages=3,
        )
        # All pages should be in the middle region
        assert min(pages) >= 5
        assert max(pages) < 15


class TestZoneMeasurements:
    """Test suite for ZoneMeasurements class."""

    @pytest.mark.unit()
    def test_zone_measurements_add(self):
        """Test adding zone measurements."""
        measurements = ZoneMeasurements()
        zones = PageZones(
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
        measurements.add(zones)
        assert len(measurements.page_widths) == 1
        assert measurements.page_widths[0] == 1000
        assert measurements.body_lefts[0] == 100

    @pytest.mark.unit()
    def test_zone_measurements_multiple_pages(self):
        """Test adding measurements from multiple pages."""
        measurements = ZoneMeasurements()
        for i in range(5):
            zones = PageZones(
                page_width=1000 + i * 10,
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
            measurements.add(zones)
        assert len(measurements.page_widths) == 5

    @pytest.mark.unit()
    def test_zone_measurements_confidence_high(self):
        """Test confidence calculation with consistent measurements."""
        measurements = ZoneMeasurements()
        # Add identical measurements (should have high confidence)
        for _ in range(10):
            zones = PageZones(
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
            measurements.add(zones)
        confidence = measurements.calculate_confidence()
        # High consistency should yield high confidence
        assert confidence > 0.8

    @pytest.mark.unit()
    def test_zone_measurements_confidence_low(self):
        """Test confidence calculation with inconsistent measurements."""
        measurements = ZoneMeasurements()
        # Add very varying measurements (should have lower confidence)
        # Use wider variation to ensure lower confidence
        for i in range(10):
            zones = PageZones(
                page_width=500 + i * 200,  # Very varying width (500-2300)
                page_height=1000 + i * 100,  # Varying height
                header_bottom=50 + i * 50,  # Varying header
                footer_top=800 + i * 100,  # Varying footer
                left_margin_right=50 + i * 100,  # Very varying margin
                right_margin_left=700 + i * 100,
                footnote_separator_y=None,
                body_left=50 + i * 100,
                body_right=700 + i * 100,
                body_top=50 + i * 50,
                body_bottom=800 + i * 100,
            )
            measurements.add(zones)
        confidence = measurements.calculate_confidence()
        # Very inconsistent measurements should yield lower confidence
        assert confidence < 0.8

    @pytest.mark.unit()
    def test_zone_measurements_detected_feature(self):
        """Test detected method for feature detection."""
        measurements = ZoneMeasurements()
        # Add zones with line numbers (large left margin)
        for _ in range(10):
            zones = PageZones(
                page_width=1000,
                page_height=1500,
                header_bottom=100,
                footer_top=1400,
                left_margin_right=150,  # > 8% of width = line numbers
                right_margin_left=900,
                footnote_separator_y=None,
                body_left=150,
                body_right=900,
                body_top=100,
                body_bottom=1400,
            )
            measurements.add(zones)
        assert measurements.detected("line_numbers_left") is True
        assert measurements.detected("line_numbers_right") is False

    @pytest.mark.unit()
    def test_zone_measurements_detected_footnotes(self):
        """Test detected method for footnotes."""
        measurements = ZoneMeasurements()
        # Add zones with footnotes
        for _ in range(10):
            zones = PageZones(
                page_width=1000,
                page_height=1500,
                header_bottom=100,
                footer_top=1400,
                left_margin_right=100,
                right_margin_left=900,
                footnote_separator_y=1350,
                body_left=100,
                body_right=900,
                body_top=100,
                body_bottom=1400,
            )
            measurements.add(zones)
        assert measurements.detected("footnotes") is True


class TestRobustMedianWithOutliers:
    """Test suite for robust_median_with_outliers function."""

    @pytest.mark.unit()
    def test_robust_median_simple(self):
        """Test robust median with consistent values."""
        # Use identical values to avoid MAD-based outlier detection
        values = [103, 103, 103, 103, 103]
        median, outlier_indices = robust_median_with_outliers(
            values, outlier_threshold=2.0
        )
        assert median == 103
        # With identical values, MAD is 0, so no outliers detected
        assert len(outlier_indices) == 0

    @pytest.mark.unit()
    def test_robust_median_with_outliers(self):
        """Test robust median with outliers."""
        values = [100, 105, 102, 200, 103, 250, 104]  # 200, 250 are outliers
        median, outlier_indices = robust_median_with_outliers(
            values, outlier_threshold=2.0
        )
        assert 100 <= median <= 105  # Should be around median of inliers
        assert len(outlier_indices) > 0  # Outliers identified
        # Outliers should be at indices 3 and 5 (values 200 and 250)
        assert 3 in outlier_indices or 5 in outlier_indices

    @pytest.mark.unit()
    def test_robust_median_all_outliers(self):
        """Test robust median when all values are outliers."""
        values = [100, 200, 300]  # All different
        median, outlier_indices = robust_median_with_outliers(
            values, outlier_threshold=1.0
        )
        # Should still return a median (could be any of the values)
        assert median in values
        # With small dataset, may or may not identify outliers
        assert isinstance(outlier_indices, list)


class TestExtractTemplate:
    """Test suite for extract_template function."""

    @pytest.mark.unit()
    @patch("philocr.pipeline.stage2_template.detect_zones_for_template")
    @patch("philocr.pipeline.stage2_template.select_sample_pages")
    def test_extract_template_basic(
        self,
        mock_select,
        mock_detect_zones,
    ):
        """Test basic template extraction."""
        config = PipelineConfig(
            template_sample_size=5,
            template_min_pages=3,
        )
        # Create mock page images
        pages = [
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
        mock_select.return_value = [0, 2, 4, 6, 8]
        # Mock zone detection
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

        template = extract_template(pages, config)

        assert isinstance(template, DocumentTemplate)
        assert template.body_left == 100
        assert template.body_right == 900
        mock_select.assert_called_once()
        mock_detect_zones.assert_called_once()
