"""Projection profile utilities for zone detection."""

from dataclasses import dataclass

import numpy as np


@dataclass
class Gap:
    """Represents a gap in a profile.

    Attributes:
        start: Start position of the gap
        end: End position of the gap
    """

    start: int
    end: int


def find_gaps(
    profile: np.ndarray,
    min_gap_size: int,
    threshold_percentile: float = 0.1,
) -> list[Gap]:
    """Find gaps (runs of low values) in a projection profile.

    Args:
        profile: 1D array of profile values
        min_gap_size: Minimum gap size in pixels to consider
        threshold_percentile: Percentile to use as "low" threshold (default 0.1)

    Returns:
        List of Gap objects (start, end positions)
    """
    if len(profile) == 0:
        return []

    # Determine threshold: values below this percentile are considered gaps
    threshold = float(np.percentile(profile, threshold_percentile * 100))

    # Find runs of values below threshold
    below_threshold = profile < threshold

    gaps: list[Gap] = []
    in_gap = False
    gap_start = 0

    for i, is_low in enumerate(below_threshold):
        if is_low and not in_gap:
            # Start of new gap
            gap_start = i
            in_gap = True
        elif not is_low and in_gap:
            # End of gap
            gap_size = i - gap_start
            if gap_size >= min_gap_size:
                gaps.append(Gap(start=gap_start, end=i))
            in_gap = False

    # Handle gap at end of profile
    if in_gap:
        gap_size = len(profile) - gap_start
        if gap_size >= min_gap_size:
            gaps.append(Gap(start=gap_start, end=len(profile)))

    return gaps
