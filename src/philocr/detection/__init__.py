"""Detection modules for zone and layout analysis."""

from philocr.detection.profiles import Gap, find_gaps
from philocr.detection.separators import (
    detect_footnote_separator,
    detect_horizontal_rule,
)
from philocr.detection.zones import (
    detect_footer_boundary,
    detect_header_boundary,
    detect_left_margin,
    detect_page_zones,
    detect_right_margin,
    find_significant_transitions,
    gaussian_smooth,
)

__all__ = [
    "Gap",
    "find_gaps",
    "detect_page_zones",
    "detect_header_boundary",
    "detect_footer_boundary",
    "detect_left_margin",
    "detect_right_margin",
    "gaussian_smooth",
    "find_significant_transitions",
    "detect_footnote_separator",
    "detect_horizontal_rule",
]
