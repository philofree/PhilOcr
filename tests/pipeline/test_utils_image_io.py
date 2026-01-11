"""Tests for image I/O utilities."""

import numpy as np
import pytest

from philocr.pipeline.utils.image_io import load_image, load_image_bytes, save_image


class TestSaveImage:
    """Test suite for save_image function."""

    @pytest.mark.unit()
    def test_save_grayscale_image(self, temp_dir):
        """Test saving a grayscale image."""
        image = np.random.randint(0, 256, (100, 150), dtype=np.uint8)
        output_path = temp_dir / "test_image.png"
        save_image(image, str(output_path))
        assert output_path.exists()

    @pytest.mark.unit()
    def test_save_creates_directory(self, temp_dir):
        """Test that save_image creates parent directories."""
        image = np.zeros((50, 50), dtype=np.uint8)
        output_path = temp_dir / "subdir" / "nested" / "test.png"
        save_image(image, str(output_path))
        assert output_path.exists()
        assert output_path.parent.exists()

    @pytest.mark.unit()
    def test_save_path_object(self, temp_dir):
        """Test that save_image accepts Path object."""
        image = np.ones((30, 40), dtype=np.uint8) * 128
        output_path = temp_dir / "test_path.png"
        save_image(image, output_path)
        assert output_path.exists()


class TestLoadImage:
    """Test suite for load_image function."""

    @pytest.mark.unit()
    def test_load_saved_image(self, temp_dir):
        """Test loading an image that was saved."""
        original = np.random.randint(0, 256, (80, 120), dtype=np.uint8)
        image_path = temp_dir / "test_load.png"
        save_image(original, str(image_path))
        loaded = load_image(str(image_path))
        assert loaded.shape == original.shape
        assert loaded.dtype == np.uint8

    @pytest.mark.unit()
    def test_load_path_object(self, temp_dir):
        """Test that load_image accepts Path object."""
        image = np.zeros((60, 80), dtype=np.uint8)
        image_path = temp_dir / "test_path_load.png"
        save_image(image, str(image_path))
        loaded = load_image(image_path)
        assert loaded.shape == image.shape

    @pytest.mark.unit()
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_image("/nonexistent/path/image.png")


class TestLoadImageBytes:
    """Test suite for load_image_bytes function."""

    @pytest.mark.unit()
    def test_load_bytes(self, temp_dir):
        """Test loading image as bytes."""
        image = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
        image_path = temp_dir / "test_bytes.png"
        save_image(image, str(image_path))
        image_bytes = load_image_bytes(str(image_path))
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    @pytest.mark.unit()
    def test_load_bytes_path_object(self, temp_dir):
        """Test that load_image_bytes accepts Path object."""
        image = np.ones((40, 40), dtype=np.uint8) * 200
        image_path = temp_dir / "test_path_bytes.png"
        save_image(image, str(image_path))
        image_bytes = load_image_bytes(image_path)
        assert isinstance(image_bytes, bytes)
