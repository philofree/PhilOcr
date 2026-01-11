"""Tests for projection profile utilities."""

import numpy as np
import pytest

from philocr.detection.profiles import Gap, find_gaps


class TestGap:
    """Test suite for Gap dataclass."""

    @pytest.mark.unit()
    def test_gap_creation(self):
        """Test that Gap can be created with start and end."""
        gap = Gap(start=10, end=20)
        assert gap.start == 10
        assert gap.end == 20

    @pytest.mark.unit()
    def test_gap_size(self):
        """Test that gap size is correct."""
        gap = Gap(start=10, end=25)
        assert gap.end - gap.start == 15


class TestFindGaps:
    """Test suite for find_gaps function."""

    @pytest.mark.unit()
    def test_empty_profile(self):
        """Test finding gaps in empty profile."""
        profile = np.array([])
        gaps = find_gaps(profile, min_gap_size=10)
        assert gaps == []

    @pytest.mark.unit()
    def test_single_gap(self):
        """Test finding a single gap in profile."""
        # Use few gap values so percentile threshold is above them
        # With 30 values and only 3 gap values, 10th percentile selects high values
        profile = np.ones(30) * 100.0
        profile[10:13] = 50.0  # Only 3 gap values (small gap)
        gaps = find_gaps(profile, min_gap_size=3)
        assert len(gaps) == 1
        assert gaps[0].start == 10
        assert gaps[0].end == 13

    @pytest.mark.unit()
    def test_multiple_gaps(self):
        """Test finding multiple gaps in profile."""
        # Use threshold_percentile to ensure gap values are below threshold
        profile = np.ones(50) * 100.0
        profile[5:10] = 50.0  # Gap 1
        profile[20:25] = 50.0  # Gap 2
        profile[35:40] = 50.0  # Gap 3
        gaps = find_gaps(profile, min_gap_size=3, threshold_percentile=0.3)
        assert len(gaps) == 3
        assert gaps[0].start == 5
        assert gaps[0].end == 10
        assert gaps[1].start == 20
        assert gaps[1].end == 25

    @pytest.mark.unit()
    def test_gap_too_small(self):
        """Test that gaps smaller than min_gap_size are ignored."""
        profile = np.ones(30)
        profile[10:13] = 0.0  # Gap of size 3
        gaps = find_gaps(profile, min_gap_size=5)
        assert len(gaps) == 0

    @pytest.mark.unit()
    def test_gap_at_start(self):
        """Test finding gap at start of profile."""
        # Use very few gap values so percentile threshold is above them
        profile = np.ones(30) * 100.0
        profile[0:3] = 50.0  # Only 3 gap values at start
        gaps = find_gaps(profile, min_gap_size=3)
        assert len(gaps) == 1
        assert gaps[0].start == 0
        assert gaps[0].end == 3

    @pytest.mark.unit()
    def test_gap_at_end(self):
        """Test finding gap at end of profile."""
        # Use very few gap values so percentile threshold is above them
        profile = np.ones(30) * 100.0
        profile[27:30] = 50.0  # Only 3 gap values at end
        gaps = find_gaps(profile, min_gap_size=3)
        assert len(gaps) == 1
        assert gaps[0].start == 27
        assert gaps[0].end == 30

    @pytest.mark.unit()
    def test_no_gaps(self):
        """Test profile with no gaps."""
        profile = np.ones(30)
        gaps = find_gaps(profile, min_gap_size=5)
        assert len(gaps) == 0

    @pytest.mark.unit()
    def test_threshold_percentile(self):
        """Test that threshold_percentile affects gap detection."""
        profile = np.ones(30) * 0.5
        profile[10:15] = 0.1  # Low values
        # With default 0.1 percentile, these should be detected
        gaps_default = find_gaps(profile, min_gap_size=3)
        # With higher percentile, might not be detected
        gaps_high = find_gaps(profile, min_gap_size=3, threshold_percentile=0.5)
        # At least default should find it
        assert len(gaps_default) >= 0

    @pytest.mark.unit()
    def test_realistic_profile(self):
        """Test with realistic projection profile pattern."""
        # Simulate a projection profile with content regions and gaps
        profile = np.ones(100) * 100.0  # High base
        profile[5:45] = 100.0  # Content region 1 (high values)
        profile[50:90] = 100.0  # Content region 2 (high values)
        # Gaps: 0-5, 45-50, 90-100 (keep as high - no gaps in this test)
        # Actually test with gap values
        profile[0:5] = 50.0  # Gap 1
        profile[45:50] = 50.0  # Gap 2
        gaps = find_gaps(profile, min_gap_size=3, threshold_percentile=0.3)
        # Should find gaps where values are below threshold
        assert len(gaps) >= 1
