"""Tests for zone detection functions."""

import numpy as np
import pytest

from philocr.detection.zones import (
    detect_footer_boundary,
    detect_header_boundary,
    detect_left_margin,
    detect_right_margin,
    find_significant_transitions,
    gaussian_smooth,
)
from philocr.models.config import PipelineConfig


class TestGaussianSmooth:
    """Test suite for gaussian_smooth function."""

    @pytest.mark.unit()
    def test_smooth_simple_signal(self):
        """Test smoothing a simple signal."""
        signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        smoothed = gaussian_smooth(signal, sigma=1.0)
        assert len(smoothed) == len(signal)
        assert smoothed.dtype == np.float64

    @pytest.mark.unit()
    def test_smooth_preserves_length(self):
        """Test that smoothing preserves array length."""
        signal = np.array([1.0] * 100)
        smoothed = gaussian_smooth(signal, sigma=2.0)
        assert len(smoothed) == 100

    @pytest.mark.unit()
    def test_smooth_no_change_with_constant(self):
        """Test that constant signal stays approximately constant."""
        signal = np.array([5.0] * 50)
        smoothed = gaussian_smooth(signal, sigma=1.0)
        # Values should be close to original (within floating point precision)
        assert np.allclose(smoothed, 5.0, atol=0.1)


class TestFindSignificantTransitions:
    """Test suite for find_significant_transitions function."""

    @pytest.mark.unit()
    def test_empty_gradient(self):
        """Test with empty gradient."""
        gradient = np.array([])
        transitions = find_significant_transitions(gradient, threshold=0.5)
        assert transitions == []

    @pytest.mark.unit()
    def test_constant_gradient(self):
        """Test with constant gradient (no transitions)."""
        gradient = np.array([0.0] * 50)
        transitions = find_significant_transitions(gradient, threshold=0.5)
        assert transitions == []

    @pytest.mark.unit()
    def test_single_transition(self):
        """Test finding a single significant transition."""
        # Create gradient with one peak
        gradient = np.zeros(50)
        gradient[20:30] = 1.0  # High gradient region
        transitions = find_significant_transitions(gradient, threshold=0.5)
        assert len(transitions) > 0

    @pytest.mark.unit()
    def test_multiple_transitions(self):
        """Test finding multiple transitions."""
        gradient = np.zeros(100)
        gradient[10:20] = 1.0  # Transition 1
        gradient[50:60] = 1.0  # Transition 2
        transitions = find_significant_transitions(gradient, threshold=0.3)
        assert len(transitions) >= 2


class TestDetectHeaderBoundary:
    """Test suite for detect_header_boundary function."""

    @pytest.mark.unit()
    def test_header_detection_with_gap(self):
        """Test header boundary detection when gap exists."""
        config = PipelineConfig(header_search_percent=0.15, min_gap_size=10)
        height = 1000
        content_top = 50
        # Create profile with gap at row 100-120 (in header region)
        h_profile = np.ones(height) * 0.8
        h_profile[100:120] = 0.0  # Gap in header region
        boundary = detect_header_boundary(h_profile, content_top, height, config)
        # Should detect gap and place boundary after it
        assert boundary >= content_top

    @pytest.mark.unit()
    def test_header_no_gap(self):
        """Test header detection when no gap exists."""
        config = PipelineConfig(header_search_percent=0.15, min_gap_size=10)
        height = 1000
        content_top = 50
        # Create profile with no gaps
        h_profile = np.ones(height) * 0.8
        boundary = detect_header_boundary(h_profile, content_top, height, config)
        # Should return content_top when no gap found
        assert boundary == content_top

    @pytest.mark.unit()
    def test_header_search_limit(self):
        """Test that header search respects search limit."""
        config = PipelineConfig(header_search_percent=0.1, min_gap_size=10)
        height = 1000
        content_top = 50
        h_profile = np.ones(height) * 0.8
        boundary = detect_header_boundary(h_profile, content_top, height, config)
        # Should not exceed search limit
        search_limit = int(height * config.header_search_percent)
        assert boundary <= content_top + search_limit


class TestDetectFooterBoundary:
    """Test suite for detect_footer_boundary function."""

    @pytest.mark.unit()
    def test_footer_detection_with_gap(self):
        """Test footer boundary detection when gap exists."""
        config = PipelineConfig(footer_search_percent=0.15, min_gap_size=10)
        height = 1000
        content_bottom = 950
        # Create profile with gap in footer region
        h_profile = np.ones(height) * 0.8
        h_profile[900:920] = 0.0  # Gap before footer
        boundary = detect_footer_boundary(h_profile, content_bottom, height, config)
        assert boundary <= content_bottom

    @pytest.mark.unit()
    def test_footer_no_gap(self):
        """Test footer detection when no gap exists."""
        config = PipelineConfig(footer_search_percent=0.15, min_gap_size=10)
        height = 1000
        content_bottom = 950
        h_profile = np.ones(height) * 0.8
        boundary = detect_footer_boundary(h_profile, content_bottom, height, config)
        assert boundary == content_bottom


class TestDetectLeftMargin:
    """Test suite for detect_left_margin function."""

    @pytest.mark.unit()
    def test_left_margin_detection(self):
        """Test left margin boundary detection."""
        config = PipelineConfig(
            margin_search_percent=0.2,
            margin_smooth_sigma=5.0,
            transition_threshold=0.5,
            margin_default_percent=0.1,
        )
        width = 1000
        content_left = 50
        # Create vertical profile with margin
        v_profile = np.zeros(width)
        v_profile[100:900] = 0.8  # Content region
        boundary = detect_left_margin(v_profile, content_left, width, config)
        # Should detect transition around 100 or use default
        assert boundary >= content_left
        assert boundary <= width


class TestDetectRightMargin:
    """Test suite for detect_right_margin function."""

    @pytest.mark.unit()
    def test_right_margin_detection(self):
        """Test right margin boundary detection."""
        config = PipelineConfig(
            margin_search_percent=0.2,
            margin_smooth_sigma=5.0,
            transition_threshold=0.5,
            margin_default_percent=0.1,
        )
        width = 1000
        content_right = 950
        # Create vertical profile with margin
        v_profile = np.zeros(width)
        v_profile[100:900] = 0.8  # Content region
        boundary = detect_right_margin(v_profile, content_right, width, config)
        # Should detect transition around 900 or use default
        assert boundary >= 0
        assert boundary <= content_right
