"""Tests for PipelineConfig model."""

import pytest

from philocr.models.config import PipelineConfig


class TestPipelineConfig:
    """Test suite for PipelineConfig dataclass."""

    @pytest.mark.unit()
    def test_default_config_creation(self):
        """Test that PipelineConfig can be created with defaults."""
        config = PipelineConfig()
        assert config.target_dpi == 300
        assert config.deskew_threshold == 0.1
        assert config.header_search_percent == 0.15
        assert config.template_sample_size == 20
        assert config.ocr_max_retries == 3
        assert config.stage1_parallel_workers == 4

    @pytest.mark.unit()
    def test_custom_config_creation(self):
        """Test that PipelineConfig can be created with custom values."""
        config = PipelineConfig(
            target_dpi=400,
            deskew_threshold=0.2,
            template_sample_size=30,
            ocr_max_retries=5,
            use_cropping=True,
        )
        assert config.target_dpi == 400
        assert config.deskew_threshold == 0.2
        assert config.template_sample_size == 30
        assert config.ocr_max_retries == 5
        assert config.use_cropping is True

    @pytest.mark.unit()
    def test_config_immutability(self):
        """Test that config fields can be modified."""
        config = PipelineConfig()
        # Dataclasses are mutable by default, so we can change values
        config.target_dpi = 400
        assert config.target_dpi == 400

    @pytest.mark.unit()
    def test_all_stage1_fields(self):
        """Test all Stage 1 configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "target_dpi")
        assert hasattr(config, "output_format")
        assert hasattr(config, "deskew_threshold")
        assert config.output_format == "PNG"

    @pytest.mark.unit()
    def test_all_stage2a_fields(self):
        """Test all Stage 2a (zone detection) configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "header_search_percent")
        assert hasattr(config, "footer_search_percent")
        assert hasattr(config, "margin_search_percent")
        assert hasattr(config, "content_threshold")
        assert hasattr(config, "min_gap_size")

    @pytest.mark.unit()
    def test_all_stage2b_fields(self):
        """Test all Stage 2b (template extraction) configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "template_sample_size")
        assert hasattr(config, "template_min_pages")
        assert hasattr(config, "template_skip_first")
        assert hasattr(config, "template_skip_last")
        assert hasattr(config, "outlier_threshold")

    @pytest.mark.unit()
    def test_all_stage2c_fields(self):
        """Test all Stage 2c (masking) configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "use_cropping")
        assert hasattr(config, "crop_padding")
        assert config.use_cropping is False  # Default is masking

    @pytest.mark.unit()
    def test_all_stage3_fields(self):
        """Test all Stage 3 (OCR) configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "ocr_max_retries")
        assert hasattr(config, "ocr_retry_backoff_base")
        assert hasattr(config, "ocr_rate_limit_per_minute")
        assert config.ocr_rate_limit_per_minute == 15

    @pytest.mark.unit()
    def test_all_stage4_fields(self):
        """Test all Stage 4 (assembly) configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "indent_ratio_threshold_1")
        assert hasattr(config, "indent_ratio_threshold_2")
        assert hasattr(config, "verse_avg_line_threshold")
        assert hasattr(config, "verse_cv_threshold")

    @pytest.mark.unit()
    def test_validation_fields(self):
        """Test validation threshold fields."""
        config = PipelineConfig()
        assert hasattr(config, "min_template_confidence")
        assert hasattr(config, "min_ocr_confidence")
        assert hasattr(config, "min_genre_confidence")
        assert config.min_template_confidence == 0.5

    @pytest.mark.unit()
    def test_performance_fields(self):
        """Test performance configuration fields."""
        config = PipelineConfig()
        assert hasattr(config, "stage1_parallel_workers")
        assert hasattr(config, "stage2a_parallel_workers")
        assert hasattr(config, "stage3_batch_size")
        assert config.stage1_parallel_workers >= 1
        assert config.stage2a_parallel_workers >= 1
