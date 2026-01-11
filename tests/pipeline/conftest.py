"""Shared fixtures for pipeline tests."""

import numpy as np
import pytest

from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage, PageZones


@pytest.fixture()
def default_config():
    """Create a default PipelineConfig for testing."""
    return PipelineConfig()


@pytest.fixture()
def sample_page_image(temp_dir):
    """Create a sample PageImage for testing."""
    return PageImage(
        page_num=0,
        path=str(temp_dir / "page_0000.png"),
        dpi=300,
        width=1000,
        height=1500,
        skew_corrected=0.0,
    )


@pytest.fixture()
def sample_page_zones():
    """Create sample PageZones for testing."""
    return PageZones(
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


@pytest.fixture()
def sample_image_array():
    """Create a sample image array for testing."""
    return np.random.randint(0, 256, (300, 400), dtype=np.uint8)


@pytest.fixture()
def mock_pdf_file(temp_dir):
    """Create a mock PDF file path."""
    pdf_path = temp_dir / "test_document.pdf"
    # Create a minimal valid PDF header
    pdf_path.write_bytes(b"%PDF-1.4\n")
    return str(pdf_path)
