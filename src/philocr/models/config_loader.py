"""Pipeline configuration loader and converter."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from philocr.models.config import PipelineConfig


def load_pipeline_config(config_dict: dict[str, Any]) -> "PipelineConfig":
    """Load PipelineConfig from configuration dictionary.

    Args:
        config_dict: Configuration dictionary with pipeline section

    Returns:
        PipelineConfig instance with loaded values

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    from philocr.models.config import PipelineConfig

    pipeline_section = config_dict.get("pipeline", {})

    # Stage 1 defaults
    stage1 = pipeline_section.get("stage1", {})
    target_dpi = stage1.get("target_dpi", 300)
    output_format = stage1.get("output_format", "PNG")
    deskew_threshold = float(stage1.get("deskew_threshold", 0.1))

    # Stage 2 defaults (cropping)
    stage2 = pipeline_section.get("stage2", {})
    use_cropping = bool(stage2.get("use_cropping", True))
    crop_padding = int(stage2.get("crop_padding", 0))

    # Stage 3 defaults (OCR)
    stage3 = pipeline_section.get("stage3", {})
    ocr_max_retries = int(stage3.get("ocr_max_retries", 3))
    ocr_retry_backoff_base = float(stage3.get("ocr_retry_backoff_base", 2.0))
    ocr_rate_limit_per_minute = int(stage3.get("ocr_rate_limit_per_minute", 15))

    # Stage 4 defaults (assembly)
    stage4 = pipeline_section.get("stage4", {})
    indent_ratio_threshold_1 = float(stage4.get("indent_ratio_threshold_1", 0.02))
    indent_ratio_threshold_2 = float(stage4.get("indent_ratio_threshold_2", 0.06))
    verse_avg_line_threshold = int(stage4.get("verse_avg_line_threshold", 60))
    verse_cv_threshold = float(stage4.get("verse_cv_threshold", 0.3))
    speaker_ratio_threshold = float(stage4.get("speaker_ratio_threshold", 0.15))
    fragment_ratio_threshold = float(stage4.get("fragment_ratio_threshold", 0.2))

    # Validation defaults
    validation = pipeline_section.get("validation", {})
    min_ocr_confidence = float(validation.get("min_ocr_confidence", 0.3))
    min_genre_confidence = float(validation.get("min_genre_confidence", 0.5))

    # Performance defaults
    performance = pipeline_section.get("performance", {})
    stage1_parallel_workers = int(performance.get("stage1_parallel_workers", 4))

    return PipelineConfig(
        target_dpi=target_dpi,
        output_format=output_format,
        deskew_threshold=deskew_threshold,
        use_cropping=use_cropping,
        crop_padding=crop_padding,
        ocr_max_retries=ocr_max_retries,
        ocr_retry_backoff_base=ocr_retry_backoff_base,
        ocr_rate_limit_per_minute=ocr_rate_limit_per_minute,
        indent_ratio_threshold_1=indent_ratio_threshold_1,
        indent_ratio_threshold_2=indent_ratio_threshold_2,
        verse_avg_line_threshold=verse_avg_line_threshold,
        verse_cv_threshold=verse_cv_threshold,
        speaker_ratio_threshold=speaker_ratio_threshold,
        fragment_ratio_threshold=fragment_ratio_threshold,
        min_ocr_confidence=min_ocr_confidence,
        min_genre_confidence=min_genre_confidence,
        stage1_parallel_workers=stage1_parallel_workers,
    )


def pipeline_config_to_dict(config: "PipelineConfig") -> dict[str, Any]:
    """Convert PipelineConfig to dictionary for saving.

    Args:
        config: PipelineConfig instance

    Returns:
        Dictionary representation suitable for YAML/JSON
    """
    return {
        "stage1": {
            "target_dpi": config.target_dpi,
            "output_format": config.output_format,
            "deskew_threshold": config.deskew_threshold,
        },
        "stage2": {
            "use_cropping": config.use_cropping,
            "crop_padding": config.crop_padding,
        },
        "stage3": {
            "ocr_max_retries": config.ocr_max_retries,
            "ocr_retry_backoff_base": config.ocr_retry_backoff_base,
            "ocr_rate_limit_per_minute": config.ocr_rate_limit_per_minute,
        },
        "stage4": {
            "indent_ratio_threshold_1": config.indent_ratio_threshold_1,
            "indent_ratio_threshold_2": config.indent_ratio_threshold_2,
            "verse_avg_line_threshold": config.verse_avg_line_threshold,
            "verse_cv_threshold": config.verse_cv_threshold,
            "speaker_ratio_threshold": config.speaker_ratio_threshold,
            "fragment_ratio_threshold": config.fragment_ratio_threshold,
        },
        "validation": {
            "min_ocr_confidence": config.min_ocr_confidence,
            "min_genre_confidence": config.min_genre_confidence,
        },
        "performance": {
            "stage1_parallel_workers": config.stage1_parallel_workers,
        },
    }
