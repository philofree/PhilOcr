"""Footnote separator detection functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from philocr.detection.profiles import find_gaps

if TYPE_CHECKING:
    from philocr.models.config import PipelineConfig


def detect_horizontal_rule(
    region: np.ndarray,
    config: PipelineConfig,
) -> int | None:
    """Detect a horizontal line (footnote separator rule).

    A horizontal rule is identified by:
    - A row with significant dark pixels (configurable minimum width)
    - Surrounded by mostly white space (above and below)
    - Thin (not multiple rows of text)

    Args:
        region: Image region to search (body lower portion)
        config: Configuration with minimum rule width threshold

    Returns:
        Y-coordinate of rule (relative to region top), or None
    """
    height, width = region.shape[:2]

    if height < 5 or width == 0:
        return None

    min_rule_width = int(width * config.horizontal_rule_min_width)

    for y in range(1, height - 3):
        row = region[y, :]

        # Check if row has a continuous dark segment
        dark_pixels = np.where(row < 128)[0]

        if len(dark_pixels) >= min_rule_width:
            # Check if it's a thin line (not text)
            # Rule should have white space above and below
            above_mean = float(np.mean(region[max(0, y - 2) : y, :]))
            below_mean = float(np.mean(region[y + 1 : min(height, y + 4), :]))

            # Both above and below should be mostly white
            if above_mean > 200 and below_mean > 200:
                return y

    return None


def detect_footnote_separator(
    image: np.ndarray,
    body_top: int,
    body_bottom: int,
    config: PipelineConfig,
) -> int | None:
    """Detect footnote separator within the body region.

    Types of separators:
    1. Horizontal rule (thin line)
    2. Large whitespace gap
    3. Row of markers (*, †, etc.)

    Args:
        image: Full page image
        body_top: Top of body region
        body_bottom: Bottom of body region
        config: Configuration with search percentage and gap thresholds

    Returns:
        Y-coordinate of footnote separator, or None if not found
    """
    body_height = body_bottom - body_top
    if body_height <= 0:
        return None

    # Search in lower N% of body region (configurable)
    search_start_percent = 1.0 - config.footnote_search_percent
    search_top = body_top + int(body_height * search_start_percent)
    search_region = image[search_top:body_bottom, :]

    if search_region.size == 0:
        return None

    # Method 1: Detect horizontal rule
    rule_y = detect_horizontal_rule(search_region, config)
    if rule_y is not None:
        return search_top + rule_y

    # Method 2: Detect large gap
    h_profile = np.sum(255 - search_region, axis=1)
    gaps = find_gaps(h_profile, config.footnote_gap_min_size)

    if gaps:
        # Use the first large gap as separator
        return search_top + gaps[0].start

    # No footnote separator detected
    return None
