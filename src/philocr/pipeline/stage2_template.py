"""Stage 2b: Template extraction from zone measurements."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage, PageZones
from philocr.models.template import DocumentTemplate
from philocr.pipeline.stage2_zones import detect_zones_for_template

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ZoneMeasurements:
    """Collects zone measurements from multiple pages for template extraction."""

    def __init__(self) -> None:
        """Initialize zone measurements collector."""
        self.page_widths: list[int] = []
        self.page_heights: list[int] = []
        self.body_lefts: list[int] = []
        self.body_rights: list[int] = []
        self.body_tops: list[int] = []
        self.body_bottoms: list[int] = []
        self.header_bottoms: list[int] = []
        self.footer_tops: list[int] = []
        self.left_margin_rights: list[int] = []
        self.right_margin_lefts: list[int] = []
        self.footnote_separators: list[int] = []
        self.has_line_numbers_left: list[bool] = []
        self.has_line_numbers_right: list[bool] = []
        self.has_footnotes: list[bool] = []

    def add(self, zones: PageZones) -> None:
        """Add measurements from a single page.

        Args:
            zones: PageZones object with detected boundaries
        """
        self.page_widths.append(zones.page_width)
        self.page_heights.append(zones.page_height)
        self.body_lefts.append(zones.body_left)
        self.body_rights.append(zones.body_right)
        self.body_tops.append(zones.body_top)
        self.body_bottoms.append(zones.body_bottom)
        self.header_bottoms.append(zones.header_bottom)
        self.footer_tops.append(zones.footer_top)
        self.left_margin_rights.append(zones.left_margin_right)
        self.right_margin_lefts.append(zones.right_margin_left)
        if zones.footnote_separator_y is not None:
            self.footnote_separators.append(zones.footnote_separator_y)
        self.has_footnotes.append(zones.footnote_separator_y is not None)

        # Line number detection heuristic: if left margin > 8% of page width,
        # likely has line numbers
        margin_ratio = (
            zones.left_margin_right / zones.page_width if zones.page_width > 0 else 0
        )
        self.has_line_numbers_left.append(margin_ratio > 0.08)
        self.has_line_numbers_right.append(False)  # Less common

    def calculate_confidence(self) -> float:
        """Calculate template confidence based on measurement consistency.

        Uses coefficient of variation (CV) across measurements.
        Lower CV = higher confidence.

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if len(self.page_widths) < 3:
            return 0.5

        # Calculate CV for key measurements
        cvs: list[float] = []
        for measurements in [
            self.page_widths,
            self.page_heights,
            self.body_lefts,
            self.body_rights,
            self.header_bottoms,
            self.footer_tops,
        ]:
            if len(measurements) > 1:
                mean_val = float(np.mean(measurements))
                std_val = float(np.std(measurements))
                cv = std_val / mean_val if mean_val > 0 else 1.0
                cvs.append(cv)

        # Confidence is inverse of average CV, capped at 1.0
        avg_cv = float(np.mean(cvs)) if cvs else 1.0
        confidence = max(0.0, min(1.0, 1.0 - avg_cv))

        return confidence

    def detected(self, feature: str) -> bool:
        """Check if a feature was detected on majority of pages.

        Args:
            feature: 'line_numbers_left', 'line_numbers_right', or 'footnotes'

        Returns:
            True if detected on >50% of pages
        """
        if feature == "line_numbers_left":
            values = self.has_line_numbers_left
        elif feature == "line_numbers_right":
            values = self.has_line_numbers_right
        elif feature == "footnotes":
            values = self.has_footnotes
        else:
            return False

        if not values:
            return False

        return sum(values) / len(values) > 0.5


def select_sample_pages(
    total_pages: int,
    sample_size: int,
    skip_first: int = 2,
    skip_last: int = 2,
    min_pages: int = 5,
) -> list[int]:
    """Select representative pages for template extraction.

    Strategy:
    - Skip first N pages (often title/contents)
    - Skip last N pages (often index/blank)
    - Distribute evenly across remaining pages
    - If document is too short, use all available pages

    Args:
        total_pages: Total number of pages in document
        sample_size: Desired number of pages to sample
        skip_first: Number of pages to skip at start
        skip_last: Number of pages to skip at end
        min_pages: Minimum pages required for sampling

    Returns:
        List of page indices (0-based) to use for template extraction
    """
    if total_pages <= min_pages:
        # Use all pages if document is short
        return list(range(total_pages))

    available = total_pages - skip_first - skip_last

    if available <= 0:
        # Fallback: skip less
        skip_first = min(skip_first, total_pages // 4)
        skip_last = min(skip_last, total_pages // 4)
        available = total_pages - skip_first - skip_last

    if available <= sample_size:
        # Not enough pages to sample; use all available
        return list(range(skip_first, total_pages - skip_last))

    # Distribute evenly across available pages
    step = available / sample_size
    indices = [skip_first + int(i * step) for i in range(sample_size)]

    return indices


def robust_median_with_outliers(
    values: list[int],
    outlier_threshold: float = 2.0,
) -> tuple[int, list[int]]:
    """Calculate median while identifying and excluding outliers.

    Uses Median Absolute Deviation (MAD) for robust outlier detection.

    Args:
        values: List of integer measurements
        outlier_threshold: Number of MADs to consider outlier (default 2.0)

    Returns:
        Tuple of (median_value, outlier_indices)
    """
    if not values:
        return 0, []

    if len(values) < 3:
        return int(np.median(values)), []

    # Calculate median and MAD
    med = float(np.median(values))
    deviations = [abs(v - med) for v in values]
    mad = float(np.median(deviations)) if deviations else 0.0

    # If MAD is zero or very small, no outliers possible
    if mad < 1.0:
        return int(med), []

    # Identify outliers
    outliers = [
        i for i, v in enumerate(values) if abs(v - med) > outlier_threshold * mad
    ]

    # Recalculate median excluding outliers if found
    if outliers and len(outliers) < len(values) / 2:
        clean_values = [v for i, v in enumerate(values) if i not in outliers]
        med = float(np.median(clean_values))

    return int(med), outliers


def extract_template(
    normalised_images: list[PageImage],
    config: PipelineConfig,
) -> DocumentTemplate:
    """Analyse multiple pages to establish consistent zone boundaries.

    Strategy:
    1. Sample pages from throughout document (avoiding title/index pages)
    2. Detect zones on each page
    3. Use robust median with outlier detection
    4. Calculate confidence based on consistency

    Args:
        normalised_images: List of normalised page images
        config: Pipeline configuration

    Returns:
        DocumentTemplate with zone boundaries and confidence score
    """
    # Sample pages evenly across document
    sample_indices = select_sample_pages(
        len(normalised_images),
        config.template_sample_size,
        config.template_skip_first,
        config.template_skip_last,
        config.template_min_pages,
    )

    # Detect zones on sampled pages
    zones_list = detect_zones_for_template(normalised_images, sample_indices, config)

    # Collect measurements
    measurements = ZoneMeasurements()
    for zones in zones_list:
        measurements.add(zones)

    # Extract template using robust statistics with outlier detection
    page_width, _ = robust_median_with_outliers(
        measurements.page_widths, config.outlier_threshold
    )
    page_height, _ = robust_median_with_outliers(
        measurements.page_heights, config.outlier_threshold
    )
    body_left, _ = robust_median_with_outliers(
        measurements.body_lefts, config.outlier_threshold
    )
    body_right, _ = robust_median_with_outliers(
        measurements.body_rights, config.outlier_threshold
    )
    body_top, _ = robust_median_with_outliers(
        measurements.body_tops, config.outlier_threshold
    )
    body_bottom, _ = robust_median_with_outliers(
        measurements.body_bottoms, config.outlier_threshold
    )
    header_bottom, _ = robust_median_with_outliers(
        measurements.header_bottoms, config.outlier_threshold
    )
    footer_top, _ = robust_median_with_outliers(
        measurements.footer_tops, config.outlier_threshold
    )
    left_margin_right, _ = robust_median_with_outliers(
        measurements.left_margin_rights, config.outlier_threshold
    )
    right_margin_left, _ = robust_median_with_outliers(
        measurements.right_margin_lefts, config.outlier_threshold
    )

    footnote_separator_y: int | None = None
    if measurements.footnote_separators:
        footnote_sep, _ = robust_median_with_outliers(
            measurements.footnote_separators, config.outlier_threshold
        )
        footnote_separator_y = footnote_sep

    template = DocumentTemplate(
        page_width=page_width,
        page_height=page_height,
        body_left=body_left,
        body_right=body_right,
        body_top=body_top,
        body_bottom=body_bottom,
        header_bottom=header_bottom,
        footer_top=footer_top,
        left_margin_right=left_margin_right,
        right_margin_left=right_margin_left,
        footnote_separator_y=footnote_separator_y,
        pages_analysed=len(sample_indices),
        confidence=measurements.calculate_confidence(),
        has_line_numbers_left=measurements.detected("line_numbers_left"),
        has_line_numbers_right=measurements.detected("line_numbers_right"),
        has_footnotes=measurements.detected("footnotes"),
    )

    logger.info(
        "template_extracted",
        pages_analysed=len(sample_indices),
        confidence=template.confidence,
        has_line_numbers_left=template.has_line_numbers_left,
        has_footnotes=template.has_footnotes,
    )

    return template


def get_default_template(
    sample_image: PageImage | None = None,
) -> DocumentTemplate:
    """Conservative default template for when extraction fails.

    Assumes:
    - 10% margins on each side
    - 5% header, 5% footer
    - No footnotes

    Args:
        sample_image: Optional sample image for dimensions

    Returns:
        DocumentTemplate with conservative defaults
    """
    if sample_image:
        width = sample_image.width
        height = sample_image.height
    else:
        # Assume 300 DPI, 8.5x11 inch page
        width = 2550
        height = 3300

    return DocumentTemplate(
        page_width=width,
        page_height=height,
        body_left=int(width * 0.10),
        body_right=int(width * 0.90),
        body_top=int(height * 0.05),
        body_bottom=int(height * 0.95),
        header_bottom=int(height * 0.05),
        footer_top=int(height * 0.95),
        left_margin_right=int(width * 0.10),
        right_margin_left=int(width * 0.90),
        footnote_separator_y=None,
        pages_analysed=0,
        confidence=0.0,
        has_line_numbers_left=False,
        has_line_numbers_right=False,
        has_footnotes=False,
    )


def apply_conservative_defaults(
    template: DocumentTemplate,
    sample_image: PageImage,
) -> DocumentTemplate:
    """Apply conservative defaults to a low-confidence template.

    Args:
        template: Existing template (may have issues)
        sample_image: Sample image for validation

    Returns:
        DocumentTemplate with expanded margins for safety
    """
    # Expand margins slightly to be safe
    margin_expansion = int(sample_image.width * 0.02)

    template.body_left = max(
        template.body_left, template.left_margin_right + margin_expansion
    )
    template.body_right = min(
        template.body_right, template.right_margin_left - margin_expansion
    )

    return template
