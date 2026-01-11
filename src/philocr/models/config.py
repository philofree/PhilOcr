"""Pipeline configuration parameters."""

from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Configuration parameters for the OCR pipeline."""

    # === STAGE 1: Image Normalisation ===
    target_dpi: int = 300
    output_format: str = "PNG"
    deskew_threshold: float = 0.1  # Degrees; only correct if > this

    # === STAGE 2a: Zone Detection ===
    header_search_percent: float = 0.15  # Search top 15% for header
    footer_search_percent: float = 0.15  # Search bottom 15% for footer
    margin_search_percent: float = 0.20  # Search outer 20% for margins
    content_threshold: float = 0.05  # Min % of row/column that must be ink
    min_gap_size: int = 20  # Pixels; minimum gap to consider significant

    # === STAGE 2a: Margin Detection ===
    margin_smooth_sigma: float = 5.0  # Gaussian smoothing sigma for profiles
    transition_threshold: float = 0.5  # Gradient threshold for margin boundary
    margin_default_percent: float = 0.05  # Default margin if detection fails

    # === STAGE 2a: Footnote Detection ===
    footnote_search_percent: float = 0.40  # Search lower 40% of body
    horizontal_rule_min_width: float = 0.2  # Min 20% of width for rule
    footnote_gap_min_size: int = 30  # Pixels; minimum gap for footnote separator

    # === STAGE 2b: Template Extraction ===
    template_sample_size: int = 20  # Pages to sample for template
    template_min_pages: int = 5  # Minimum pages required
    template_skip_first: int = 2  # Skip first N pages (often title/contents)
    template_skip_last: int = 2  # Skip last N pages (often index/blank)
    outlier_threshold: float = 2.0  # MAD multiplier for outlier detection

    # === STAGE 2c: Masking Strategy ===
    use_cropping: bool = False  # True = crop, False = mask (default)
    crop_padding: int = 0  # Extra pixels around body when cropping

    # === STAGE 3: OCR ===
    ocr_max_retries: int = 3
    ocr_retry_backoff_base: float = 2.0  # Exponential backoff multiplier
    ocr_rate_limit_per_minute: int = 15

    # === STAGE 4: Assembly ===
    indent_ratio_threshold_1: float = 0.02  # < 2% = flush left
    indent_ratio_threshold_2: float = 0.06  # < 6% = standard indent

    # === STAGE 4: Genre Detection (Heuristic) ===
    verse_avg_line_threshold: int = 60  # Chars; below suggests verse
    verse_cv_threshold: float = 0.3  # Coefficient of variation; below suggests verse
    speaker_ratio_threshold: float = 0.15  # Ratio of lines with speaker markers
    fragment_ratio_threshold: float = 0.2  # Ratio of fragment markers to paragraphs

    # === Validation ===
    min_template_confidence: float = 0.5  # Below this, use defaults
    min_ocr_confidence: float = 0.3  # Below this, flag for review
    min_genre_confidence: float = 0.5  # Below this, default to prose

    # === Performance ===
    stage1_parallel_workers: int = 4
    stage2a_parallel_workers: int = 4
    stage3_batch_size: int = 1  # For future batch API support
