"""Zone detection functions for template extraction."""

from typing import TYPE_CHECKING

import numpy as np
from scipy.ndimage import gaussian_filter1d  # type: ignore[import-untyped]

from philocr.detection.profiles import find_gaps

if TYPE_CHECKING:
    from philocr.models.config import PipelineConfig
    from philocr.models.page import PageZones


def gaussian_smooth(signal: np.ndarray, sigma: float) -> np.ndarray:
    """Apply Gaussian smoothing to a 1D signal.

    Uses scipy.ndimage.gaussian_filter1d for efficient smoothing.

    Args:
        signal: 1D array to smooth
        sigma: Standard deviation of Gaussian kernel

    Returns:
        Smoothed signal (same length as input)
    """
    return gaussian_filter1d(signal.astype(float), sigma=sigma)


def find_significant_transitions(
    gradient: np.ndarray,
    threshold: float,
) -> list[int]:
    """Find significant transition points in a gradient signal.

    Args:
        gradient: 1D array of gradient values
        threshold: Minimum gradient magnitude to consider significant

    Returns:
        List of indices where significant transitions occur
    """
    if len(gradient) == 0:
        return []

    # Normalize gradient to [0, 1] for threshold comparison
    abs_gradient = np.abs(gradient)
    max_grad = float(np.max(abs_gradient))

    if max_grad == 0:
        return []

    normalized = abs_gradient / max_grad

    # Find peaks above threshold
    above_threshold = normalized > threshold

    # Find indices where gradient crosses threshold
    transitions: list[int] = []
    for i in range(1, len(above_threshold)):
        if above_threshold[i] and not above_threshold[i - 1]:
            # Rising edge
            transitions.append(i)
        elif not above_threshold[i] and above_threshold[i - 1]:
            # Falling edge
            transitions.append(i - 1)

    return sorted(set(transitions))


def detect_header_boundary(
    h_profile: np.ndarray,
    content_top: int,
    height: int,
    config: "PipelineConfig",
) -> int:
    """Find where header ends and body begins.

    Strategy: Look for a significant gap in the horizontal profile
    within the top N% of the page (configurable).

    Args:
        h_profile: Horizontal projection profile (sum of pixels per row)
        content_top: First row with content
        height: Total page height
        config: Configuration with search percentage and gap threshold

    Returns:
        Y-coordinate where header zone ends
    """
    search_limit = int(height * config.header_search_percent)
    search_limit = min(search_limit, content_top + search_limit)

    if search_limit <= content_top:
        return content_top

    # Find gaps (runs of low values) in the profile
    search_region = h_profile[content_top:search_limit]
    gaps = find_gaps(search_region, config.min_gap_size)

    if gaps:
        # Header ends at the first significant gap
        return content_top + gaps[0].end
    else:
        # No clear header; use top of content
        return content_top


def detect_footer_boundary(
    h_profile: np.ndarray,
    content_bottom: int,
    height: int,
    config: "PipelineConfig",
) -> int:
    """Find where body ends and footer begins.

    Strategy: Look for a significant gap in the horizontal profile
    within the bottom N% of the page (configurable).

    Args:
        h_profile: Horizontal projection profile
        content_bottom: Last row with content
        height: Total page height
        config: Configuration with search percentage and gap threshold

    Returns:
        Y-coordinate where footer zone starts
    """
    search_start = int(height * (1 - config.footer_search_percent))
    search_start = max(
        search_start, content_bottom - int(height * config.footer_search_percent)
    )

    if search_start >= content_bottom:
        return content_bottom

    # Find gaps in the profile (searching backwards from bottom)
    search_region = h_profile[search_start:content_bottom]
    gaps = find_gaps(search_region, config.min_gap_size)

    if gaps:
        # Footer starts at the last significant gap
        return search_start + gaps[-1].start
    else:
        # No clear footer; use bottom of content
        return content_bottom


def detect_left_margin(
    v_profile: np.ndarray,
    content_left: int,
    width: int,
    config: "PipelineConfig",
) -> int:
    """HEURISTIC: Detect left margin boundary (where line numbers end, body begins).

    Strategy:
    1. Line numbers form a narrow column of sparse content
    2. Body text forms a dense column
    3. Find the transition point using gradient analysis

    Args:
        v_profile: Vertical projection profile (sum of pixels per column)
        content_left: Leftmost column with content
        width: Total page width
        config: Configuration with search percentage and thresholds

    Returns:
        X-coordinate where left margin ends (body begins)
    """
    search_limit = int(width * config.margin_search_percent)
    search_limit = min(search_limit, content_left + search_limit)

    if search_limit <= content_left:
        return content_left + int(width * config.margin_default_percent)

    # Smooth the profile to reduce noise
    search_region = v_profile[:search_limit]
    smoothed = gaussian_smooth(search_region, config.margin_smooth_sigma)

    # Find the column where density increases significantly (body starts)
    # This is typically a step change in the profile
    gradient = np.gradient(smoothed)

    # Find largest positive gradient (transition from sparse to dense)
    transition_points = find_significant_transitions(
        gradient, config.transition_threshold
    )

    if transition_points:
        return content_left + transition_points[0]
    else:
        # No clear margin; use default percentage
        return content_left + int(width * config.margin_default_percent)


def detect_right_margin(
    v_profile: np.ndarray,
    content_right: int,
    width: int,
    config: "PipelineConfig",
) -> int:
    """Detect right margin boundary.

    Similar to left margin but searching from the right.

    Args:
        v_profile: Vertical projection profile
        content_right: Rightmost column with content
        width: Total page width
        config: Configuration with search percentage and thresholds

    Returns:
        X-coordinate where right margin starts (body ends)
    """
    search_start = int(width * (1 - config.margin_search_percent))
    search_start = max(
        search_start, content_right - int(width * config.margin_search_percent)
    )

    if search_start >= content_right:
        return content_right - int(width * config.margin_default_percent)

    # Search region is from search_start to end
    search_region = v_profile[search_start:]
    smoothed = gaussian_smooth(search_region, config.margin_smooth_sigma)
    gradient = np.gradient(smoothed)

    # Find largest negative gradient (transition from dense to sparse)
    # Negate gradient to find where it drops (transition from body to margin)
    transition_points = find_significant_transitions(
        -gradient, config.transition_threshold
    )

    if transition_points:
        return search_start + transition_points[-1]
    else:
        return content_right - int(width * config.margin_default_percent)


def detect_page_zones(image: np.ndarray, config: "PipelineConfig") -> "PageZones":
    """Detect zones on a single page using projection profiles.

    Args:
        image: Grayscale image (numpy array, 0-255)
        config: Pipeline configuration with detection thresholds

    Returns:
        PageZones dataclass with detected boundaries
    """
    from philocr.detection.separators import detect_footnote_separator
    from philocr.models.page import PageZones

    height, width = image.shape[:2]

    # Horizontal projection (sum across rows) → find vertical boundaries
    h_profile = np.sum(255 - image, axis=1).astype(float)

    # Vertical projection (sum across columns) → find horizontal boundaries
    v_profile = np.sum(255 - image, axis=0).astype(float)

    # Normalize profiles to [0, 1] for threshold comparison
    h_max = float(np.max(h_profile))
    v_max = float(np.max(v_profile))
    h_profile_norm = h_profile / h_max if h_max > 0 else h_profile
    v_profile_norm = v_profile / v_max if v_max > 0 else v_profile

    # Find content boundaries using threshold
    content_threshold = config.content_threshold
    content_rows = np.where(h_profile_norm > content_threshold)[0]
    content_cols = np.where(v_profile_norm > content_threshold)[0]

    content_top = int(content_rows[0]) if len(content_rows) > 0 else 0
    content_bottom = int(content_rows[-1]) if len(content_rows) > 0 else height
    content_left = int(content_cols[0]) if len(content_cols) > 0 else 0
    content_right = int(content_cols[-1]) if len(content_cols) > 0 else width

    # Detect header zone (isolated content at top)
    header_bottom = detect_header_boundary(h_profile, content_top, height, config)

    # Detect footer zone (isolated content at bottom)
    footer_top = detect_footer_boundary(h_profile, content_bottom, height, config)

    # Detect left margin (narrow column of content, typically line numbers)
    left_margin_right = detect_left_margin(v_profile, content_left, width, config)

    # Detect right margin
    right_margin_left = detect_right_margin(v_profile, content_right, width, config)

    # Detect footnote separator (horizontal gap or rule in lower body)
    footnote_sep = detect_footnote_separator(image, header_bottom, footer_top, config)

    return PageZones(
        page_width=width,
        page_height=height,
        header_bottom=header_bottom,
        footer_top=footer_top,
        left_margin_right=left_margin_right,
        right_margin_left=right_margin_left,
        footnote_separator_y=footnote_sep,
        body_left=left_margin_right,
        body_right=right_margin_left,
        body_top=header_bottom,
        body_bottom=footnote_sep if footnote_sep else footer_top,
    )
