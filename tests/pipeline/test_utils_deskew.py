"""Tests for deskewing utilities."""

import numpy as np
import pytest

from philocr.pipeline.utils.deskew import detect_skew, rotate_image


class TestDetectSkew:
    """Test suite for detect_skew function."""

    @pytest.mark.unit()
    def test_no_skew(self):
        """Test detecting skew in a perfectly aligned image."""
        # Create a simple image with horizontal lines
        image = np.zeros((200, 300), dtype=np.uint8)
        image[50, :] = 255  # Horizontal line
        image[100, :] = 255
        image[150, :] = 255
        angle = detect_skew(image)
        # Should be close to 0 for horizontal lines
        assert abs(angle) < 5.0

    @pytest.mark.unit()
    def test_small_image(self):
        """Test with image too small for reliable detection."""
        image = np.ones((20, 20), dtype=np.uint8) * 128
        angle = detect_skew(image)
        # Should return 0.0 for images with insufficient content
        assert angle == 0.0

    @pytest.mark.unit()
    def test_image_with_content(self):
        """Test that function returns a valid angle."""
        # Create image with some content
        image = np.random.randint(0, 256, (300, 400), dtype=np.uint8)
        # Add some structure
        image[100:200, :] = 200
        angle = detect_skew(image)
        # Should return a valid angle (not NaN or inf)
        assert np.isfinite(angle)
        assert -90 <= angle <= 90


class TestRotateImage:
    """Test suite for rotate_image function."""

    @pytest.mark.unit()
    def test_no_rotation(self):
        """Test rotating by 0 degrees."""
        image = np.random.randint(0, 256, (100, 150), dtype=np.uint8)
        rotated = rotate_image(image, 0.0)
        assert rotated.shape == image.shape
        # Should be very similar (allowing for slight interpolation differences)
        assert np.allclose(rotated, image, atol=5)

    @pytest.mark.unit()
    def test_rotate_90_degrees(self):
        """Test rotating by 90 degrees."""
        image = np.zeros((100, 150), dtype=np.uint8)
        image[50, :] = 255  # Horizontal line
        rotated = rotate_image(image, 90.0)
        assert rotated.shape == image.shape
        # After 90 degree rotation, horizontal line becomes vertical
        # Check that middle column has high values
        assert np.max(rotated[:, 75]) > 100

    @pytest.mark.unit()
    def test_rotate_preserves_shape(self):
        """Test that rotation preserves image dimensions."""
        image = np.random.randint(0, 256, (200, 300), dtype=np.uint8)
        rotated = rotate_image(image, 45.0)
        assert rotated.shape == image.shape

    @pytest.mark.unit()
    def test_rotate_small_angle(self):
        """Test rotating by a small angle."""
        image = np.random.randint(0, 256, (100, 150), dtype=np.uint8)
        rotated = rotate_image(image, 5.0)
        assert rotated.shape == image.shape
        # Should still be mostly similar
        assert np.std(rotated) > 0

    @pytest.mark.unit()
    def test_rotate_negative_angle(self):
        """Test rotating by negative angle."""
        image = np.random.randint(0, 256, (100, 150), dtype=np.uint8)
        rotated = rotate_image(image, -10.0)
        assert rotated.shape == image.shape
