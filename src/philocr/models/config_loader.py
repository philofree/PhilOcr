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

    # Stage 2a defaults
    stage2a = pipeline_section.get("stage2a", {})
    header_search_percent = float(stage2a.get("header_search_percent", 0.15))
    footer_search_percent = float(stage2a.get("footer_search_percent", 0.15))
    margin_search_percent = float(stage2a.get("margin_search_percent", 0.20))
    content_threshold = float(stage2a.get("content_threshold", 0.05))
    min_gap_size = int(stage2a.get("min_gap_size", 20))
    margin_smooth_sigma = float(stage2a.get("margin_smooth_sigma", 5.0))
    transition_threshold = float(stage2a.get("transition_threshold", 0.5))
    margin_default_percent = float(stage2a.get("margin_default_percent", 0.05))
    footnote_search_percent = float(stage2a.get("footnote_search_percent", 0.40))
    horizontal_rule_min_width = float(stage2a.get("horizontal_rule_min_width", 0.2))
    footnote_gap_min_size = int(stage2a.get("footnote_gap_min_size", 30))

    # Stage 2b defaults
    stage2b = pipeline_section.get("stage2b", {})
    template_sample_size = int(stage2b.get("template_sample_size", 20))
    template_min_pages = int(stage2b.get("template_min_pages", 5))
    template_skip_first = int(stage2b.get("template_skip_first", 2))
    template_skip_last = int(stage2b.get("template_skip_last", 2))
    outlier_threshold = float(stage2b.get("outlier_threshold", 2.0))

    # Stage 2c defaults
    stage2c = pipeline_section.get("stage2c", {})
    use_cropping = bool(stage2c.get("use_cropping", False))
    crop_padding = int(stage2c.get("crop_padding", 0))

    # Stage 3 defaults
    stage3 = pipeline_section.get("stage3", {})
    ocr_max_retries = int(stage3.get("ocr_max_retries", 3))
    ocr_retry_backoff_base = float(stage3.get("ocr_retry_backoff_base", 2.0))
    ocr_rate_limit_per_minute = int(stage3.get("ocr_rate_limit_per_minute", 15))

    # Stage 4 defaults
    stage4 = pipeline_section.get("stage4", {})
    indent_ratio_threshold_1 = float(stage4.get("indent_ratio_threshold_1", 0.02))
    indent_ratio_threshold_2 = float(stage4.get("indent_ratio_threshold_2", 0.06))
    verse_avg_line_threshold = int(stage4.get("verse_avg_line_threshold", 60))
    verse_cv_threshold = float(stage4.get("verse_cv_threshold", 0.3))
    speaker_ratio_threshold = float(stage4.get("speaker_ratio_threshold", 0.15))
    fragment_ratio_threshold = float(stage4.get("fragment_ratio_threshold", 0.2))

    # Validation defaults
    validation = pipeline_section.get("validation", {})
    min_template_confidence = float(validation.get("min_template_confidence", 0.5))
    min_ocr_confidence = float(validation.get("min_ocr_confidence", 0.3))
    min_genre_confidence = float(validation.get("min_genre_confidence", 0.5))

    # Performance defaults
    performance = pipeline_section.get("performance", {})
    stage1_parallel_workers = int(performance.get("stage1_parallel_workers", 4))
    stage2a_parallel_workers = int(performance.get("stage2a_parallel_workers", 4))
    stage3_batch_size = int(performance.get("stage3_batch_size", 1))

    return PipelineConfig(
        target_dpi=target_dpi,
        output_format=output_format,
        deskew_threshold=deskew_threshold,
        header_search_percent=header_search_percent,
        footer_search_percent=footer_search_percent,
        margin_search_percent=margin_search_percent,
        content_threshold=content_threshold,
        min_gap_size=min_gap_size,
        margin_smooth_sigma=margin_smooth_sigma,
        transition_threshold=transition_threshold,
        margin_default_percent=margin_default_percent,
        footnote_search_percent=footnote_search_percent,
        horizontal_rule_min_width=horizontal_rule_min_width,
        footnote_gap_min_size=footnote_gap_min_size,
        template_sample_size=template_sample_size,
        template_min_pages=template_min_pages,
        template_skip_first=template_skip_first,
        template_skip_last=template_skip_last,
        outlier_threshold=outlier_threshold,
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
        min_template_confidence=min_template_confidence,
        min_ocr_confidence=min_ocr_confidence,
        min_genre_confidence=min_genre_confidence,
        stage1_parallel_workers=stage1_parallel_workers,
        stage2a_parallel_workers=stage2a_parallel_workers,
        stage3_batch_size=stage3_batch_size,
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
        "stage2a": {
            "header_search_percent": config.header_search_percent,
            "footer_search_percent": config.footer_search_percent,
            "margin_search_percent": config.margin_search_percent,
            "content_threshold": config.content_threshold,
            "min_gap_size": config.min_gap_size,
            "margin_smooth_sigma": config.margin_smooth_sigma,
            "transition_threshold": config.transition_threshold,
            "margin_default_percent": config.margin_default_percent,
            "footnote_search_percent": config.footnote_search_percent,
            "horizontal_rule_min_width": config.horizontal_rule_min_width,
            "footnote_gap_min_size": config.footnote_gap_min_size,
        },
        "stage2b": {
            "template_sample_size": config.template_sample_size,
            "template_min_pages": config.template_min_pages,
            "template_skip_first": config.template_skip_first,
            "template_skip_last": config.template_skip_last,
            "outlier_threshold": config.outlier_threshold,
        },
        "stage2c": {
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
            "min_template_confidence": config.min_template_confidence,
            "min_ocr_confidence": config.min_ocr_confidence,
            "min_genre_confidence": config.min_genre_confidence,
        },
        "performance": {
            "stage1_parallel_workers": config.stage1_parallel_workers,
            "stage2a_parallel_workers": config.stage2a_parallel_workers,
            "stage3_batch_size": config.stage3_batch_size,
        },
    }
