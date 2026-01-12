"""Pipeline configuration parameters."""

from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Configuration parameters for the OCR pipeline.

    The pipeline now uses manual scan areas defined by the user,
    so automatic zone detection settings have been removed.
    """

    # === STAGE 1: Image Normalisation ===
    target_dpi: int = 300
    output_format: str = "PNG"
    deskew_threshold: float = 0.1  # Degrees; only correct if > this

    # === STAGE 2: Masking/Cropping ===
    use_cropping: bool = True  # True = crop to scan area, False = mask
    crop_padding: int = 0  # Extra pixels around scan area when cropping

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
    min_ocr_confidence: float = 0.3  # Below this, flag for review
    min_genre_confidence: float = 0.5  # Below this, default to prose

    # === Performance ===
    stage1_parallel_workers: int = 4
